"""
Unit tests for DataEnricher.

Tests parallel enrichment of orders and products with ThreadPoolExecutor,
error handling, and resilience.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from concurrent.futures import ThreadPoolExecutor
from src.data_enricher import DataEnricher


class TestDataEnricherInitialization:
    """Tests for DataEnricher initialization."""
    
    def test_init_with_valid_max_workers(self):
        """Test initialization with valid max_workers."""
        client = Mock()
        enricher = DataEnricher(client, max_workers=5)
        
        assert enricher.client == client
        assert enricher.max_workers == 5
    
    def test_init_with_default_max_workers(self):
        """Test initialization uses default max_workers=5."""
        client = Mock()
        enricher = DataEnricher(client)
        
        assert enricher.max_workers == 5
    
    def test_init_with_invalid_max_workers(self):
        """Test initialization with invalid max_workers raises ValueError."""
        client = Mock()
        
        with pytest.raises(ValueError, match="max_workers debe ser mayor que 0"):
            DataEnricher(client, max_workers=0)
        
        with pytest.raises(ValueError, match="max_workers debe ser mayor que 0"):
            DataEnricher(client, max_workers=-1)


class TestFetchOrderItems:
    """Tests for _fetch_order_items method."""
    
    def test_fetch_order_items_success(self):
        """Test successful fetch of order items."""
        client = Mock()
        client.get.return_value = {
            "data": [
                {"id": "item-1", "name": "Item 1"},
                {"id": "item-2", "name": "Item 2"}
            ]
        }
        
        enricher = DataEnricher(client)
        items = enricher._fetch_order_items("order-123")
        
        assert items is not None
        assert len(items) == 2
        assert items[0]["id"] == "item-1"
        client.get.assert_called_once_with("orders/order-123/items")
    
    def test_fetch_order_items_empty_response(self):
        """Test fetch with empty items list."""
        client = Mock()
        client.get.return_value = {"data": []}
        
        enricher = DataEnricher(client)
        items = enricher._fetch_order_items("order-123")
        
        assert items == []
    
    def test_fetch_order_items_api_error(self):
        """Test fetch returns None on API error."""
        client = Mock()
        client.get.side_effect = Exception("API Error")
        
        enricher = DataEnricher(client)
        items = enricher._fetch_order_items("order-123")
        
        assert items is None
    
    def test_fetch_order_items_missing_data_key(self):
        """Test fetch handles missing 'data' key in response."""
        client = Mock()
        client.get.return_value = {}
        
        enricher = DataEnricher(client)
        items = enricher._fetch_order_items("order-123")
        
        assert items == []


class TestFetchProductSkus:
    """Tests for _fetch_product_skus method."""
    
    def test_fetch_product_skus_success(self):
        """Test successful fetch of product SKUs."""
        client = Mock()
        client.get.return_value = {
            "data": [
                {"id": "sku-1", "name": "SKU 1"},
                {"id": "sku-2", "name": "SKU 2"}
            ]
        }
        
        enricher = DataEnricher(client)
        skus = enricher._fetch_product_skus("product-123")
        
        assert skus is not None
        assert len(skus) == 2
        assert skus[0]["id"] == "sku-1"
        client.get.assert_called_once_with("products/product-123/skus")
    
    def test_fetch_product_skus_empty_response(self):
        """Test fetch with empty SKUs list."""
        client = Mock()
        client.get.return_value = {"data": []}
        
        enricher = DataEnricher(client)
        skus = enricher._fetch_product_skus("product-123")
        
        assert skus == []
    
    def test_fetch_product_skus_api_error(self):
        """Test fetch returns None on API error."""
        client = Mock()
        client.get.side_effect = Exception("API Error")
        
        enricher = DataEnricher(client)
        skus = enricher._fetch_product_skus("product-123")
        
        assert skus is None


class TestEnrichOrders:
    """Tests for enrich_orders method."""
    
    def test_enrich_orders_empty_list(self):
        """Test enrichment of empty list."""
        client = Mock()
        enricher = DataEnricher(client)
        
        result = enricher.enrich_orders([])
        
        assert result == []
        client.get.assert_not_called()
    
    def test_enrich_orders_success(self):
        """Test successful enrichment of orders."""
        client = Mock()
        client.get.return_value = {
            "data": [
                {"id": "item-1", "quantity": 2}
            ]
        }
        
        enricher = DataEnricher(client)
        orders = [
            {"id": "order-1", "status": "new"},
            {"id": "order-2", "status": "pending"}
        ]
        
        enriched = enricher.enrich_orders(orders)
        
        assert len(enriched) == 2
        assert enriched[0]["id"] == "order-1"
        assert enriched[0]["_enrichment_complete"] is True
        assert "_items" in enriched[0]
        assert enriched[1]["id"] == "order-2"
        assert enriched[1]["_enrichment_complete"] is True
    
    def test_enrich_orders_preserves_order(self):
        """Test that enrichment preserves original order."""
        client = Mock()
        client.get.return_value = {"data": [{"id": "item-1"}]}
        
        enricher = DataEnricher(client)
        orders = [
            {"id": "order-1", "index": 0},
            {"id": "order-2", "index": 1},
            {"id": "order-3", "index": 2}
        ]
        
        enriched = enricher.enrich_orders(orders)
        
        assert len(enriched) == 3
        assert enriched[0]["index"] == 0
        assert enriched[1]["index"] == 1
        assert enriched[2]["index"] == 2
    
    def test_enrich_orders_with_api_error(self):
        """Test enrichment handles API errors gracefully."""
        client = Mock()
        client.get.side_effect = Exception("API Error")
        
        enricher = DataEnricher(client)
        orders = [{"id": "order-1", "status": "new"}]
        
        enriched = enricher.enrich_orders(orders)
        
        assert len(enriched) == 1
        assert enriched[0]["id"] == "order-1"
        assert enriched[0]["_enrichment_complete"] is False
        assert enriched[0]["_items"] == []
    
    def test_enrich_orders_without_id(self):
        """Test enrichment handles orders without ID."""
        client = Mock()
        
        enricher = DataEnricher(client)
        orders = [
            {"status": "new"},  # No ID
            {"id": "order-2", "status": "pending"}
        ]
        
        client.get.return_value = {"data": [{"id": "item-1"}]}
        enriched = enricher.enrich_orders(orders)
        
        assert len(enriched) == 2
        assert enriched[0]["_enrichment_complete"] is False
        assert enriched[0]["_items"] == []
        assert enriched[1]["_enrichment_complete"] is True
    
    def test_enrich_orders_partial_failure(self):
        """Test enrichment with some orders failing."""
        client = Mock()
        
        # First call succeeds, second fails
        client.get.side_effect = [
            {"data": [{"id": "item-1"}]},
            Exception("API Error")
        ]
        
        enricher = DataEnricher(client)
        orders = [
            {"id": "order-1", "status": "new"},
            {"id": "order-2", "status": "pending"}
        ]
        
        enriched = enricher.enrich_orders(orders)
        
        assert len(enriched) == 2
        # One should succeed, one should fail
        success_count = sum(1 for o in enriched if o["_enrichment_complete"])
        failure_count = sum(1 for o in enriched if not o["_enrichment_complete"])
        assert success_count == 1
        assert failure_count == 1
    
    def test_enrich_orders_preserves_original_fields(self):
        """Test that enrichment preserves all original fields."""
        client = Mock()
        client.get.return_value = {"data": [{"id": "item-1"}]}
        
        enricher = DataEnricher(client)
        orders = [{
            "id": "order-1",
            "status": "new",
            "totalAmount": 100.0,
            "customer": {"name": "John"}
        }]
        
        enriched = enricher.enrich_orders(orders)
        
        assert enriched[0]["id"] == "order-1"
        assert enriched[0]["status"] == "new"
        assert enriched[0]["totalAmount"] == 100.0
        assert enriched[0]["customer"]["name"] == "John"
        assert "_items" in enriched[0]
        assert "_enrichment_complete" in enriched[0]


class TestEnrichProducts:
    """Tests for enrich_products method."""
    
    def test_enrich_products_empty_list(self):
        """Test enrichment of empty list."""
        client = Mock()
        enricher = DataEnricher(client)
        
        result = enricher.enrich_products([])
        
        assert result == []
        client.get.assert_not_called()
    
    def test_enrich_products_success(self):
        """Test successful enrichment of products."""
        client = Mock()
        client.get.return_value = {
            "data": [
                {"id": "sku-1", "name": "SKU 1"}
            ]
        }
        
        enricher = DataEnricher(client)
        products = [
            {"id": "product-1", "name": "Product 1"},
            {"id": "product-2", "name": "Product 2"}
        ]
        
        enriched = enricher.enrich_products(products)
        
        assert len(enriched) == 2
        assert enriched[0]["id"] == "product-1"
        assert enriched[0]["_enrichment_complete"] is True
        assert "_skus" in enriched[0]
        assert enriched[1]["id"] == "product-2"
        assert enriched[1]["_enrichment_complete"] is True
    
    def test_enrich_products_preserves_order(self):
        """Test that enrichment preserves original order."""
        client = Mock()
        client.get.return_value = {"data": [{"id": "sku-1"}]}
        
        enricher = DataEnricher(client)
        products = [
            {"id": "product-1", "index": 0},
            {"id": "product-2", "index": 1},
            {"id": "product-3", "index": 2}
        ]
        
        enriched = enricher.enrich_products(products)
        
        assert len(enriched) == 3
        assert enriched[0]["index"] == 0
        assert enriched[1]["index"] == 1
        assert enriched[2]["index"] == 2
    
    def test_enrich_products_with_api_error(self):
        """Test enrichment handles API errors gracefully."""
        client = Mock()
        client.get.side_effect = Exception("API Error")
        
        enricher = DataEnricher(client)
        products = [{"id": "product-1", "name": "Product 1"}]
        
        enriched = enricher.enrich_products(products)
        
        assert len(enriched) == 1
        assert enriched[0]["id"] == "product-1"
        assert enriched[0]["_enrichment_complete"] is False
        assert enriched[0]["_skus"] == []
    
    def test_enrich_products_without_id(self):
        """Test enrichment handles products without ID."""
        client = Mock()
        
        enricher = DataEnricher(client)
        products = [
            {"name": "Product 1"},  # No ID
            {"id": "product-2", "name": "Product 2"}
        ]
        
        client.get.return_value = {"data": [{"id": "sku-1"}]}
        enriched = enricher.enrich_products(products)
        
        assert len(enriched) == 2
        assert enriched[0]["_enrichment_complete"] is False
        assert enriched[0]["_skus"] == []
        assert enriched[1]["_enrichment_complete"] is True
    
    def test_enrich_products_partial_failure(self):
        """Test enrichment with some products failing."""
        client = Mock()
        
        # First call succeeds, second fails
        client.get.side_effect = [
            {"data": [{"id": "sku-1"}]},
            Exception("API Error")
        ]
        
        enricher = DataEnricher(client)
        products = [
            {"id": "product-1", "name": "Product 1"},
            {"id": "product-2", "name": "Product 2"}
        ]
        
        enriched = enricher.enrich_products(products)
        
        assert len(enriched) == 2
        # One should succeed, one should fail
        success_count = sum(1 for p in enriched if p["_enrichment_complete"])
        failure_count = sum(1 for p in enriched if not p["_enrichment_complete"])
        assert success_count == 1
        assert failure_count == 1


class TestParallelization:
    """Tests for parallel execution with ThreadPoolExecutor."""
    
    def test_uses_thread_pool_executor(self):
        """Test that enrichment uses ThreadPoolExecutor."""
        client = Mock()
        client.get.return_value = {"data": []}
        
        enricher = DataEnricher(client, max_workers=3)
        orders = [{"id": f"order-{i}"} for i in range(5)]
        
        with patch('src.data_enricher.ThreadPoolExecutor') as mock_executor:
            mock_executor.return_value.__enter__.return_value.submit.return_value.result.return_value = []
            enricher.enrich_orders(orders)
            
            # Verify ThreadPoolExecutor was created with correct max_workers
            mock_executor.assert_called_with(max_workers=3)
    
    def test_respects_max_workers_setting(self):
        """Test that max_workers setting is respected."""
        client = Mock()
        client.get.return_value = {"data": []}
        
        enricher = DataEnricher(client, max_workers=10)
        assert enricher.max_workers == 10


class TestResilienceAndErrorHandling:
    """Tests for resilience and error handling."""
    
    def test_never_loses_records(self):
        """Test that enrichment never loses records, even on error."""
        client = Mock()
        client.get.side_effect = Exception("API Error")
        
        enricher = DataEnricher(client)
        orders = [{"id": f"order-{i}"} for i in range(10)]
        
        enriched = enricher.enrich_orders(orders)
        
        # Should return same number of records
        assert len(enriched) == len(orders)
        # All should be marked as incomplete
        assert all(not o["_enrichment_complete"] for o in enriched)
    
    def test_enrichment_complete_flag_accuracy(self):
        """Test that _enrichment_complete flag is accurate."""
        client = Mock()
        
        # Alternate between success and failure
        responses = [
            {"data": [{"id": "item-1"}]},
            Exception("Error"),
            {"data": [{"id": "item-2"}]},
            Exception("Error")
        ]
        client.get.side_effect = responses
        
        enricher = DataEnricher(client)
        orders = [{"id": f"order-{i}"} for i in range(4)]
        
        enriched = enricher.enrich_orders(orders)
        
        # Check that flags match actual success/failure
        for order in enriched:
            if order["_enrichment_complete"]:
                assert len(order["_items"]) > 0
            else:
                assert order["_items"] == []


class TestEdgeCases:
    """Tests for edge cases."""
    
    def test_single_order_enrichment(self):
        """Test enrichment of single order."""
        client = Mock()
        client.get.return_value = {"data": [{"id": "item-1"}]}
        
        enricher = DataEnricher(client)
        orders = [{"id": "order-1"}]
        
        enriched = enricher.enrich_orders(orders)
        
        assert len(enriched) == 1
        assert enriched[0]["_enrichment_complete"] is True
    
    def test_large_batch_enrichment(self):
        """Test enrichment of large batch."""
        client = Mock()
        client.get.return_value = {"data": [{"id": "item-1"}]}
        
        enricher = DataEnricher(client, max_workers=5)
        orders = [{"id": f"order-{i}"} for i in range(100)]
        
        enriched = enricher.enrich_orders(orders)
        
        assert len(enriched) == 100
        assert all(o["_enrichment_complete"] for o in enriched)
    
    def test_enrichment_with_none_values(self):
        """Test enrichment handles None values in records."""
        client = Mock()
        client.get.return_value = {"data": []}
        
        enricher = DataEnricher(client)
        orders = [{"id": "order-1", "status": None, "amount": None}]
        
        enriched = enricher.enrich_orders(orders)
        
        assert len(enriched) == 1
        assert enriched[0]["status"] is None
        assert enriched[0]["amount"] is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
