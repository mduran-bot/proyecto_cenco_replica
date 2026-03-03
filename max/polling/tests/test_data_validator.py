"""
Unit tests for DataValidator.

Tests schema validation, business rules, duplicate detection,
and batch validation for all 5 entity types.
"""

import pytest
import os
import json
from unittest.mock import Mock, patch
from src.data_validator import DataValidator, BUSINESS_RULES


class TestDataValidatorInitialization:
    """Tests for DataValidator initialization."""
    
    def test_init_with_valid_data_type(self):
        """Test initialization with valid data type."""
        validator = DataValidator("orders")
        assert validator.data_type == "orders"
        assert validator.schema is not None
        assert validator.validator is not None
    
    def test_init_with_invalid_data_type(self):
        """Test initialization with invalid data type raises ValueError."""
        with pytest.raises(ValueError, match="no soportado"):
            DataValidator("invalid_type")
    
    def test_init_loads_schema_correctly(self):
        """Test that schema is loaded correctly from file."""
        validator = DataValidator("products")
        assert "$schema" in validator.schema
        assert validator.schema["title"] == "Product"
    
    def test_init_with_custom_schemas_dir(self, tmp_path):
        """Test initialization with custom schemas directory."""
        # Create temporary schema file
        schema_dir = tmp_path / "schemas"
        schema_dir.mkdir()
        schema_file = schema_dir / "orders.json"
        
        test_schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {"id": {"type": "string"}},
            "required": ["id"]
        }
        
        with open(schema_file, "w") as f:
            json.dump(test_schema, f)
        
        validator = DataValidator("orders", schemas_dir=str(schema_dir))
        assert validator.schema == test_schema
    
    def test_init_with_missing_schema_file(self, tmp_path):
        """Test initialization with missing schema file raises FileNotFoundError."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        
        with pytest.raises(FileNotFoundError):
            DataValidator("orders", schemas_dir=str(empty_dir))


class TestSchemaValidation:
    """Tests for JSON schema validation."""
    
    def test_validate_valid_order(self):
        """Test validation of valid order record."""
        validator = DataValidator("orders")
        
        valid_order = {
            "id": "123",
            "status": "new",
            "totalAmount": 100.0,
            "items": [
                {"purchasedPrice": 50.0, "purchasedQuantity": 2}
            ],
            "dateCreated": "2024-01-15T10:00:00Z",
            "dateModified": "2024-01-15T10:00:00Z"
        }
        
        is_valid, errors = validator.validate_record(valid_order)
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_order_missing_required_field(self):
        """Test validation fails when required field is missing."""
        validator = DataValidator("orders")
        
        invalid_order = {
            "id": "123",
            "status": "new",
            # Missing totalAmount (required)
            "items": [{"purchasedPrice": 50.0, "purchasedQuantity": 2}],
            "dateCreated": "2024-01-15T10:00:00Z",
            "dateModified": "2024-01-15T10:00:00Z"
        }
        
        is_valid, errors = validator.validate_record(invalid_order)
        assert is_valid is False
        assert len(errors) > 0
        assert any("totalAmount" in str(e) for e in errors)
    
    def test_validate_order_invalid_status_enum(self):
        """Test validation fails with invalid enum value."""
        validator = DataValidator("orders")
        
        invalid_order = {
            "id": "123",
            "status": "invalid_status",  # Not in enum
            "totalAmount": 100.0,
            "items": [{"purchasedPrice": 50.0, "purchasedQuantity": 2}],
            "dateCreated": "2024-01-15T10:00:00Z",
            "dateModified": "2024-01-15T10:00:00Z"
        }
        
        is_valid, errors = validator.validate_record(invalid_order)
        assert is_valid is False
        assert any("status" in str(e) for e in errors)
    
    def test_validate_product_valid(self):
        """Test validation of valid product record."""
        validator = DataValidator("products")
        
        valid_product = {
            "id": "prod-123",
            "name": "Test Product",
            "referenceId": "ref-123",
            "brand": "brand-123",
            "category": "cat-123",
            "status": "active",
            "dateCreated": "2024-01-15T10:00:00Z",
            "dateModified": "2024-01-15T10:00:00Z"
        }
        
        is_valid, errors = validator.validate_record(valid_product)
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_stock_valid(self):
        """Test validation of valid stock record."""
        validator = DataValidator("stock")
        
        valid_stock = {
            "id": "stock-123",
            "skuId": "sku-123",
            "skuCatalogId": "cat-sku-123",
            "quantity": 100,
            "accountId": "acc-123",
            "dateCreated": "2024-01-15T10:00:00Z",
            "dateModified": "2024-01-15T10:00:00Z"
        }
        
        is_valid, errors = validator.validate_record(valid_stock)
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_price_valid(self):
        """Test validation of valid price record."""
        validator = DataValidator("prices")
        
        valid_price = {
            "id": "price-123",
            "skuCatalogId": "sku-cat-123",
            "accountId": "acc-123",
            "price": 99.99,
            "status": "active",
            "dateCreated": "2024-01-15T10:00:00Z",
            "dateModified": "2024-01-15T10:00:00Z"
        }
        
        is_valid, errors = validator.validate_record(valid_price)
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_store_valid(self):
        """Test validation of valid store record."""
        validator = DataValidator("stores")
        
        valid_store = {
            "id": "store-123",
            "name": "Test Store",
            "referenceId": "ref-store-123",
            "locationId": "loc-123",
            "status": "active",
            "dateCreated": "2024-01-15T10:00:00Z",
            "dateModified": "2024-01-15T10:00:00Z"
        }
        
        is_valid, errors = validator.validate_record(valid_store)
        assert is_valid is True
        assert len(errors) == 0


class TestBusinessRules:
    """Tests for business rules validation."""
    
    def test_order_total_amount_positive(self):
        """Test order totalAmount must be positive."""
        validator = DataValidator("orders")
        
        invalid_order = {
            "id": "123",
            "status": "new",
            "totalAmount": 0,  # Should be > 0
            "items": [{"purchasedPrice": 50.0, "purchasedQuantity": 2}],
            "dateCreated": "2024-01-15T10:00:00Z",
            "dateModified": "2024-01-15T10:00:00Z"
        }
        
        is_valid, errors = validator.validate_record(invalid_order)
        assert is_valid is False
        assert any("totalAmount debe ser mayor a 0" in str(e) for e in errors)
    
    def test_order_items_not_empty(self):
        """Test order must have at least one item."""
        validator = DataValidator("orders")
        
        invalid_order = {
            "id": "123",
            "status": "new",
            "totalAmount": 100.0,
            "items": [],  # Should have at least 1 item
            "dateCreated": "2024-01-15T10:00:00Z",
            "dateModified": "2024-01-15T10:00:00Z"
        }
        
        is_valid, errors = validator.validate_record(invalid_order)
        assert is_valid is False
        assert any("al menos un ítem" in str(e) for e in errors)
    
    def test_order_item_quantities_positive(self):
        """Test order item quantities must be positive."""
        validator = DataValidator("orders")
        
        invalid_order = {
            "id": "123",
            "status": "new",
            "totalAmount": 100.0,
            "items": [
                {"purchasedPrice": 50.0, "purchasedQuantity": 0}  # Should be > 0
            ],
            "dateCreated": "2024-01-15T10:00:00Z",
            "dateModified": "2024-01-15T10:00:00Z"
        }
        
        is_valid, errors = validator.validate_record(invalid_order)
        assert is_valid is False
        assert any("purchasedQuantity > 0" in str(e) for e in errors)
    
    def test_product_name_not_empty(self):
        """Test product name cannot be empty."""
        validator = DataValidator("products")
        
        invalid_product = {
            "id": "prod-123",
            "name": "   ",  # Empty after strip
            "referenceId": "ref-123",
            "brand": "brand-123",
            "category": "cat-123",
            "status": "active",
            "dateCreated": "2024-01-15T10:00:00Z",
            "dateModified": "2024-01-15T10:00:00Z"
        }
        
        is_valid, errors = validator.validate_record(invalid_product)
        assert is_valid is False
        assert any("name no puede estar vacío" in str(e) for e in errors)
    
    def test_stock_quantity_non_negative(self):
        """Test stock quantity cannot be negative."""
        validator = DataValidator("stock")
        
        invalid_stock = {
            "id": "stock-123",
            "skuId": "sku-123",
            "skuCatalogId": "cat-sku-123",
            "quantity": -10,  # Should be >= 0
            "accountId": "acc-123",
            "dateCreated": "2024-01-15T10:00:00Z",
            "dateModified": "2024-01-15T10:00:00Z"
        }
        
        is_valid, errors = validator.validate_record(invalid_stock)
        assert is_valid is False
        assert any("quantity no puede ser negativo" in str(e) for e in errors)
    
    def test_stock_available_lte_quantity(self):
        """Test stock availableQuantity cannot exceed quantity."""
        validator = DataValidator("stock")
        
        invalid_stock = {
            "id": "stock-123",
            "skuId": "sku-123",
            "skuCatalogId": "cat-sku-123",
            "quantity": 100,
            "availableQuantity": 150,  # Should be <= quantity
            "accountId": "acc-123",
            "dateCreated": "2024-01-15T10:00:00Z",
            "dateModified": "2024-01-15T10:00:00Z"
        }
        
        is_valid, errors = validator.validate_record(invalid_stock)
        assert is_valid is False
        assert any("availableQuantity no puede ser mayor que quantity" in str(e) for e in errors)
    
    def test_price_positive(self):
        """Test price must be positive."""
        validator = DataValidator("prices")
        
        invalid_price = {
            "id": "price-123",
            "skuCatalogId": "sku-cat-123",
            "accountId": "acc-123",
            "price": 0,  # Should be > 0
            "status": "active",
            "dateCreated": "2024-01-15T10:00:00Z",
            "dateModified": "2024-01-15T10:00:00Z"
        }
        
        is_valid, errors = validator.validate_record(invalid_price)
        assert is_valid is False
        assert any("price debe ser mayor a 0" in str(e) for e in errors)
    
    def test_price_valid_dates_order(self):
        """Test price validFrom must be before validTo."""
        validator = DataValidator("prices")
        
        invalid_price = {
            "id": "price-123",
            "skuCatalogId": "sku-cat-123",
            "accountId": "acc-123",
            "price": 99.99,
            "status": "active",
            "validFrom": "2024-12-31T00:00:00Z",
            "validTo": "2024-01-01T00:00:00Z",  # Before validFrom
            "dateCreated": "2024-01-15T10:00:00Z",
            "dateModified": "2024-01-15T10:00:00Z"
        }
        
        is_valid, errors = validator.validate_record(invalid_price)
        assert is_valid is False
        assert any("validFrom debe ser anterior" in str(e) for e in errors)


class TestDuplicateDetection:
    """Tests for duplicate detection in batch."""
    
    def test_detect_no_duplicates(self):
        """Test detection with no duplicates."""
        validator = DataValidator("orders")
        
        records = [
            {"id": "123", "status": "new"},
            {"id": "456", "status": "new"},
            {"id": "789", "status": "new"}
        ]
        
        unique, dup_count = validator.detect_duplicates(records)
        assert len(unique) == 3
        assert dup_count == 0
    
    def test_detect_simple_duplicates(self):
        """Test detection of simple duplicates."""
        validator = DataValidator("orders")
        
        records = [
            {"id": "123", "status": "new"},
            {"id": "123", "status": "updated"},  # Duplicate
            {"id": "456", "status": "new"}
        ]
        
        unique, dup_count = validator.detect_duplicates(records)
        assert len(unique) == 2
        assert dup_count == 1
        # Should keep first occurrence
        assert unique[0]["id"] == "123"
        assert unique[0]["status"] == "new"
    
    def test_detect_multiple_duplicates(self):
        """Test detection of multiple duplicates of same ID."""
        validator = DataValidator("orders")
        
        records = [
            {"id": "123", "version": "v1"},
            {"id": "123", "version": "v2"},
            {"id": "123", "version": "v3"},
            {"id": "456", "version": "v1"}
        ]
        
        unique, dup_count = validator.detect_duplicates(records)
        assert len(unique) == 2
        assert dup_count == 2
    
    def test_detect_duplicates_with_missing_id(self):
        """Test detection handles records without ID."""
        validator = DataValidator("orders")
        
        records = [
            {"id": "123", "status": "new"},
            {"status": "no-id"},  # No ID
            {"id": "456", "status": "new"}
        ]
        
        unique, dup_count = validator.detect_duplicates(records)
        assert len(unique) == 3  # All kept, can't deduplicate without ID
        assert dup_count == 0


class TestValidateBatch:
    """Tests for batch validation."""
    
    def test_validate_empty_batch(self):
        """Test validation of empty batch."""
        validator = DataValidator("orders")
        
        valid_records, metrics = validator.validate_batch([])
        
        assert len(valid_records) == 0
        assert metrics["total_received"] == 0
        assert metrics["valid_count"] == 0
        assert metrics["validation_pass_rate"] == 100.0
    
    def test_validate_batch_all_valid(self):
        """Test validation of batch with all valid records."""
        validator = DataValidator("orders")
        
        records = [
            {
                "id": "123",
                "status": "new",
                "totalAmount": 100.0,
                "items": [{"purchasedPrice": 50.0, "purchasedQuantity": 2}],
                "dateCreated": "2024-01-15T10:00:00Z",
                "dateModified": "2024-01-15T10:00:00Z"
            },
            {
                "id": "456",
                "status": "new",
                "totalAmount": 200.0,
                "items": [{"purchasedPrice": 100.0, "purchasedQuantity": 2}],
                "dateCreated": "2024-01-15T10:00:00Z",
                "dateModified": "2024-01-15T10:00:00Z"
            }
        ]
        
        valid_records, metrics = validator.validate_batch(records)
        
        assert len(valid_records) == 2
        assert metrics["total_received"] == 2
        assert metrics["duplicates_in_batch"] == 0
        assert metrics["valid_count"] == 2
        assert metrics["invalid_count"] == 0
        assert metrics["validation_pass_rate"] == 100.0
    
    def test_validate_batch_with_invalid_records(self):
        """Test validation of batch with some invalid records."""
        validator = DataValidator("orders")
        
        records = [
            {
                "id": "123",
                "status": "new",
                "totalAmount": 100.0,
                "items": [{"purchasedPrice": 50.0, "purchasedQuantity": 2}],
                "dateCreated": "2024-01-15T10:00:00Z",
                "dateModified": "2024-01-15T10:00:00Z"
            },
            {
                "id": "456",
                "status": "new",
                "totalAmount": 0,  # Invalid: should be > 0
                "items": [{"purchasedPrice": 50.0, "purchasedQuantity": 2}],
                "dateCreated": "2024-01-15T10:00:00Z",
                "dateModified": "2024-01-15T10:00:00Z"
            }
        ]
        
        valid_records, metrics = validator.validate_batch(records)
        
        assert len(valid_records) == 1
        assert metrics["valid_count"] == 1
        assert metrics["invalid_count"] == 1
        assert metrics["validation_pass_rate"] == 50.0
        assert len(metrics["invalid_records"]) == 1
        assert metrics["invalid_records"][0]["id"] == "456"
    
    def test_validate_batch_with_duplicates(self):
        """Test validation of batch with duplicates."""
        validator = DataValidator("orders")
        
        records = [
            {
                "id": "123",
                "status": "new",
                "totalAmount": 100.0,
                "items": [{"purchasedPrice": 50.0, "purchasedQuantity": 2}],
                "dateCreated": "2024-01-15T10:00:00Z",
                "dateModified": "2024-01-15T10:00:00Z"
            },
            {
                "id": "123",  # Duplicate
                "status": "updated",
                "totalAmount": 150.0,
                "items": [{"purchasedPrice": 75.0, "purchasedQuantity": 2}],
                "dateCreated": "2024-01-15T10:00:00Z",
                "dateModified": "2024-01-15T10:00:00Z"
            },
            {
                "id": "456",
                "status": "new",
                "totalAmount": 200.0,
                "items": [{"purchasedPrice": 100.0, "purchasedQuantity": 2}],
                "dateCreated": "2024-01-15T10:00:00Z",
                "dateModified": "2024-01-15T10:00:00Z"
            }
        ]
        
        valid_records, metrics = validator.validate_batch(records)
        
        assert metrics["total_received"] == 3
        assert metrics["duplicates_in_batch"] == 1
        assert metrics["total_after_dedup"] == 2
        assert metrics["valid_count"] == 2
    
    def test_validate_batch_metrics_structure(self):
        """Test that batch validation returns correct metrics structure."""
        validator = DataValidator("products")
        
        records = [
            {
                "id": "prod-123",
                "name": "Test Product",
                "referenceId": "ref-123",
                "brand": "brand-123",
                "category": "cat-123",
                "status": "active",
                "dateCreated": "2024-01-15T10:00:00Z",
                "dateModified": "2024-01-15T10:00:00Z"
            }
        ]
        
        _, metrics = validator.validate_batch(records)
        
        # Verify all expected keys are present
        assert "total_received" in metrics
        assert "duplicates_in_batch" in metrics
        assert "total_after_dedup" in metrics
        assert "valid_count" in metrics
        assert "invalid_count" in metrics
        assert "validation_pass_rate" in metrics
        assert "invalid_records" in metrics


class TestAllEntityTypes:
    """Tests validation for all 5 entity types."""
    
    def test_orders_validation(self):
        """Test orders validation works correctly."""
        validator = DataValidator("orders")
        assert validator.data_type == "orders"
        assert validator.schema["title"] == "Order"
    
    def test_products_validation(self):
        """Test products validation works correctly."""
        validator = DataValidator("products")
        assert validator.data_type == "products"
        assert validator.schema["title"] == "Product"
    
    def test_stock_validation(self):
        """Test stock validation works correctly."""
        validator = DataValidator("stock")
        assert validator.data_type == "stock"
        assert validator.schema["title"] == "Stock"
    
    def test_prices_validation(self):
        """Test prices validation works correctly."""
        validator = DataValidator("prices")
        assert validator.data_type == "prices"
        assert validator.schema["title"] == "Price"
    
    def test_stores_validation(self):
        """Test stores validation works correctly."""
        validator = DataValidator("stores")
        assert validator.data_type == "stores"
        assert validator.schema["title"] == "Store"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
