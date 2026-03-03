"""
DataEnricher - Enriquecedor de datos para el Sistema de Polling de APIs de Janis.

Este módulo implementa enriquecimiento paralelo de registros usando ThreadPoolExecutor,
obteniendo datos relacionados (items de órdenes, SKUs de productos) desde la API de Janis.

Requirements:
- 7.1: Enriquecer órdenes con sus items via orders/{id}/items
- 7.2: Enriquecer productos con sus SKUs via products/{id}/skus
- 7.3: Paralelización con ThreadPoolExecutor (max_workers=5)
- 7.4: Manejo de errores resiliente con _enrichment_complete flag
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class DataEnricher:
    """
    Enriquecedor de datos para órdenes y productos del sistema de polling.

    Obtiene datos relacionados desde la API de Janis en paralelo usando
    ThreadPoolExecutor. Si el enriquecimiento de un registro falla, el registro
    se incluye igualmente con el flag `_enrichment_complete=False`, garantizando
    que no se pierdan registros por errores de enriquecimiento.

    Attributes:
        client: Instancia de JanisAPIClient para realizar requests
        max_workers (int): Número máximo de workers para ThreadPoolExecutor
    """

    def __init__(self, client, max_workers: int = 5):
        """
        Inicializa el enriquecedor de datos.

        Args:
            client: Instancia de JanisAPIClient con rate limiting configurado
            max_workers: Número máximo de threads paralelos (default: 5)

        Raises:
            ValueError: Si max_workers es menor o igual a 0
        """
        if max_workers <= 0:
            raise ValueError("max_workers debe ser mayor que 0")

        self.client = client
        self.max_workers = max_workers

        logger.info(f"DataEnricher inicializado con max_workers={max_workers}")

    # -------------------------------------------------------------------------
    # Métodos auxiliares privados
    # -------------------------------------------------------------------------

    def _fetch_order_items(self, order_id: str) -> Optional[List[Dict]]:
        """
        Obtiene los items de una orden desde la API.

        Llama al endpoint `orders/{order_id}/items` y retorna la lista
        de items. En caso de error retorna None para que el caller pueda
        marcar el enriquecimiento como incompleto.

        Requirements:
        - 7.1: Obtener items de órdenes via orders/{id}/items

        Args:
            order_id: ID de la orden a enriquecer

        Returns:
            List[Dict] con los items, o None si ocurrió un error
        """
        try:
            response = self.client.get(f"orders/{order_id}/items")
            items = response.get("data", [])
            logger.debug(f"Order {order_id}: {len(items)} items obtenidos")
            return items
        except Exception as e:
            logger.error(
                f"Error obteniendo items de orden {order_id}: {e}",
                exc_info=True
            )
            return None

    def _fetch_product_skus(self, product_id: str) -> Optional[List[Dict]]:
        """
        Obtiene los SKUs de un producto desde la API.

        Llama al endpoint `products/{product_id}/skus` y retorna la lista
        de SKUs. En caso de error retorna None para que el caller pueda
        marcar el enriquecimiento como incompleto.

        Requirements:
        - 7.2: Obtener SKUs de productos via products/{id}/skus

        Args:
            product_id: ID del producto a enriquecer

        Returns:
            List[Dict] con los SKUs, o None si ocurrió un error
        """
        try:
            response = self.client.get(f"products/{product_id}/skus")
            skus = response.get("data", [])
            logger.debug(f"Product {product_id}: {len(skus)} SKUs obtenidos")
            return skus
        except Exception as e:
            logger.error(
                f"Error obteniendo SKUs de producto {product_id}: {e}",
                exc_info=True
            )
            return None

    # -------------------------------------------------------------------------
    # Métodos públicos de enriquecimiento
    # -------------------------------------------------------------------------

    def enrich_orders(self, orders: List[Dict]) -> List[Dict]:
        """
        Enriquece una lista de órdenes con sus items en paralelo.

        Para cada orden, obtiene los items desde `orders/{id}/items` usando
        ThreadPoolExecutor. Cada orden enriquecida recibe:
        - `_items`: lista de items obtenidos (vacía si hubo error)
        - `_enrichment_complete`: True si el enriquecimiento fue exitoso,
          False si ocurrió algún error (la orden se incluye igual)

        Requirements:
        - 7.1: Enriquecer órdenes con sus items
        - 7.3: Usar ThreadPoolExecutor con max_workers=5
        - 7.4: Manejo resiliente de errores con _enrichment_complete flag

        Args:
            orders: Lista de órdenes a enriquecer

        Returns:
            List[Dict]: Órdenes con campos de enriquecimiento agregados.
                        Siempre retorna la misma cantidad de registros recibidos.

        Example:
            >>> enricher = DataEnricher(api_client)
            >>> enriched = enricher.enrich_orders(orders)
            >>> # Cada orden tendrá: order['_items'] y order['_enrichment_complete']
        """
        if not orders:
            logger.debug("enrich_orders llamado con lista vacía")
            return []

        logger.info(f"Iniciando enriquecimiento de {len(orders)} órdenes (max_workers={self.max_workers})")

        enriched_orders = [None] * len(orders)
        success_count = 0
        error_count = 0

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Mapear future → índice para preservar orden
            future_to_index = {
                executor.submit(self._fetch_order_items, order.get("id")): idx
                for idx, order in enumerate(orders)
                if order.get("id")
            }

            # Registros sin ID: marcar como incompletos directamente
            for idx, order in enumerate(orders):
                if not order.get("id"):
                    logger.warning(f"Orden sin 'id' en índice {idx}, no se puede enriquecer")
                    enriched_order = dict(order)
                    enriched_order["_items"] = []
                    enriched_order["_enrichment_complete"] = False
                    enriched_orders[idx] = enriched_order
                    error_count += 1

            for future in as_completed(future_to_index):
                idx = future_to_index[future]
                order = orders[idx]
                enriched_order = dict(order)

                try:
                    items = future.result()

                    if items is not None:
                        enriched_order["_items"] = items
                        enriched_order["_enrichment_complete"] = True
                        success_count += 1
                    else:
                        # _fetch_order_items retornó None → hubo error
                        enriched_order["_items"] = []
                        enriched_order["_enrichment_complete"] = False
                        error_count += 1

                except Exception as e:
                    logger.error(
                        f"Error inesperado enriqueciendo orden {order.get('id')}: {e}",
                        exc_info=True
                    )
                    enriched_order["_items"] = []
                    enriched_order["_enrichment_complete"] = False
                    error_count += 1

                enriched_orders[idx] = enriched_order

        logger.info(
            f"Enriquecimiento de órdenes completado: "
            f"{success_count} exitosos, {error_count} con errores "
            f"de {len(orders)} totales"
        )

        return enriched_orders

    def enrich_products(self, products: List[Dict]) -> List[Dict]:
        """
        Enriquece una lista de productos con sus SKUs en paralelo.

        Para cada producto, obtiene los SKUs desde `products/{id}/skus` usando
        ThreadPoolExecutor. Cada producto enriquecido recibe:
        - `_skus`: lista de SKUs obtenidos (vacía si hubo error)
        - `_enrichment_complete`: True si el enriquecimiento fue exitoso,
          False si ocurrió algún error (el producto se incluye igual)

        Requirements:
        - 7.2: Enriquecer productos con sus SKUs
        - 7.3: Usar ThreadPoolExecutor con max_workers=5
        - 7.4: Manejo resiliente de errores con _enrichment_complete flag

        Args:
            products: Lista de productos a enriquecer

        Returns:
            List[Dict]: Productos con campos de enriquecimiento agregados.
                        Siempre retorna la misma cantidad de registros recibidos.

        Example:
            >>> enricher = DataEnricher(api_client)
            >>> enriched = enricher.enrich_products(products)
            >>> # Cada producto tendrá: product['_skus'] y product['_enrichment_complete']
        """
        if not products:
            logger.debug("enrich_products llamado con lista vacía")
            return []

        logger.info(f"Iniciando enriquecimiento de {len(products)} productos (max_workers={self.max_workers})")

        enriched_products = [None] * len(products)
        success_count = 0
        error_count = 0

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Mapear future → índice para preservar orden
            future_to_index = {
                executor.submit(self._fetch_product_skus, product.get("id")): idx
                for idx, product in enumerate(products)
                if product.get("id")
            }

            # Registros sin ID: marcar como incompletos directamente
            for idx, product in enumerate(products):
                if not product.get("id"):
                    logger.warning(f"Producto sin 'id' en índice {idx}, no se puede enriquecer")
                    enriched_product = dict(product)
                    enriched_product["_skus"] = []
                    enriched_product["_enrichment_complete"] = False
                    enriched_products[idx] = enriched_product
                    error_count += 1

            for future in as_completed(future_to_index):
                idx = future_to_index[future]
                product = products[idx]
                enriched_product = dict(product)

                try:
                    skus = future.result()

                    if skus is not None:
                        enriched_product["_skus"] = skus
                        enriched_product["_enrichment_complete"] = True
                        success_count += 1
                    else:
                        # _fetch_product_skus retornó None → hubo error
                        enriched_product["_skus"] = []
                        enriched_product["_enrichment_complete"] = False
                        error_count += 1

                except Exception as e:
                    logger.error(
                        f"Error inesperado enriqueciendo producto {product.get('id')}: {e}",
                        exc_info=True
                    )
                    enriched_product["_skus"] = []
                    enriched_product["_enrichment_complete"] = False
                    error_count += 1

                enriched_products[idx] = enriched_product

        logger.info(
            f"Enriquecimiento de productos completado: "
            f"{success_count} exitosos, {error_count} con errores "
            f"de {len(products)} totales"
        )

        return enriched_products
