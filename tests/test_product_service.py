import pytest
from app.models.category import Category
from app.models.product import Product
from app.schemas.product_schema import ProductUpdate
from app.services.product_service import ProductService
from tests.conftest import db_session


@pytest.fixture
def sample_category(db_session):
    category = Category(name="Test Category", slug="test-category")
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)
    return category


@pytest.fixture
def sample_products(db_session, sample_category):
    products = [
        Product(name="iPhone 15", description="Apple flagship phone", price=999.99, stock=10, category_id=sample_category.id, slug="iphone-15"),
        Product(name="Samsung Galaxy S24", description="Android flagship", price=799.99, stock=5, category_id=sample_category.id, slug="samsung-galaxy-s24"),
        Product(name="Budget Phone", description="Cheap Android device", price=149.99, stock=0, category_id=sample_category.id, slug="budget-phone"),
    ]
    db_session.add_all(products)
    db_session.commit()
    for p in products:
        db_session.refresh(p)
    return products


class TestGetProductsAdvanced:

    def test_search_by_name(self, db_session, sample_products):
        service = ProductService(db_session)
        result = service.get_products_advanced(search="iPhone")
        assert result["total_items"] == 1
        assert result["items"][0].name == "iPhone 15"

    def test_search_by_description(self, db_session, sample_products):
        service = ProductService(db_session)
        result = service.get_products_advanced(search="flagship")
        assert result["total_items"] == 2

    def test_filter_by_category(self, db_session, sample_products, sample_category):
        service = ProductService(db_session)
        result = service.get_products_advanced(category_id=sample_category.id)
        assert result["total_items"] == 3

    def test_filter_by_category_no_match(self, db_session, sample_products):
        service = ProductService(db_session)
        result = service.get_products_advanced(category_id=99999)
        assert result["total_items"] == 0

    def test_filter_by_min_price(self, db_session, sample_products):
        service = ProductService(db_session)
        result = service.get_products_advanced(min_price=500)
        assert result["total_items"] == 2

    def test_filter_by_max_price(self, db_session, sample_products):
        service = ProductService(db_session)
        result = service.get_products_advanced(max_price=200)
        assert result["total_items"] == 1
        assert result["items"][0].name == "Budget Phone"

    def test_filter_by_price_range(self, db_session, sample_products):
        service = ProductService(db_session)
        result = service.get_products_advanced(min_price=150, max_price=900)
        assert result["total_items"] == 1
        assert result["items"][0].name == "Samsung Galaxy S24"

    def test_sort_by_price_ascending(self, db_session, sample_products):
        service = ProductService(db_session)
        result = service.get_products_advanced(sort_by="price", sort_order="asc")
        prices = [float(p.price) for p in result["items"]]
        assert prices == sorted(prices)

    def test_sort_by_price_descending(self, db_session, sample_products):
        service = ProductService(db_session)
        result = service.get_products_advanced(sort_by="price", sort_order="desc")
        prices = [float(p.price) for p in result["items"]]
        assert prices == sorted(prices, reverse=True)

    def test_sort_by_invalid_field_falls_back_to_id(self, db_session, sample_products):
        # sort_by="hacked_field" exist nahi karta Product model mein, to "id" pe fallback hona chahiye
        service = ProductService(db_session)
        result = service.get_products_advanced(sort_by="nonexistent_field", sort_order="desc")
        assert result["total_items"] == 3  # crash nahi hona chahiye

    def test_pagination_first_page(self, db_session, sample_products):
        service = ProductService(db_session)
        result = service.get_products_advanced(page=1, limit=2)
        assert len(result["items"]) == 2
        assert result["total_items"] == 3
        assert result["total_pages"] == 2

    def test_pagination_second_page(self, db_session, sample_products):
        service = ProductService(db_session)
        result = service.get_products_advanced(page=2, limit=2)
        assert len(result["items"]) == 1

    def test_combined_search_filter_sort_pagination(self, db_session, sample_products):
        service = ProductService(db_session)
        result = service.get_products_advanced(
            search="Android", sort_by="price", sort_order="asc", page=1, limit=10
        )
        assert result["total_items"] == 2
        assert result["items"][0].name == "Budget Phone"  # cheapest Android pehle


class TestProductUpdate:

    def test_update_nonexistent_product_returns_none(self, db_session):
        service = ProductService(db_session)
        result = service.update(product_id=99999, obj_in=ProductUpdate(name="Doesn't matter"))
        assert result is None

    def test_update_name_regenerates_slug(self, db_session, sample_products):
        service = ProductService(db_session)
        product = sample_products[0]
        updated = service.update(product_id=product.id, obj_in=ProductUpdate(name="iPhone 15 Pro Max"))
        assert updated.name == "iPhone 15 Pro Max"
        assert updated.slug == "iphone-15-pro-max"

    def test_update_price_only_keeps_slug_unchanged(self, db_session, sample_products):
        service = ProductService(db_session)
        product = sample_products[0]
        original_slug = product.slug
        updated = service.update(product_id=product.id, obj_in=ProductUpdate(price=1099.99))
        assert float(updated.price) == 1099.99
        assert updated.slug == original_slug

    def test_update_stock(self, db_session, sample_products):
        service = ProductService(db_session)
        product = sample_products[2]
        updated = service.update(product_id=product.id, obj_in=ProductUpdate(stock=25))
        assert updated.stock == 25

    def test_update_is_active_flag(self, db_session, sample_products):
        service = ProductService(db_session)
        product = sample_products[0]
        updated = service.update(product_id=product.id, obj_in=ProductUpdate(is_active=False))
        assert updated.is_active is False
        

class TestProductCreate:

    def test_create_product_generates_correct_slug(self, db_session, sample_category):
        service = ProductService(db_session)
        from app.schemas.product_schema import ProductCreate
        obj_in = ProductCreate(
            name="Samsung Galaxy S25 FE!",
            description="Test description",
            price=599.99,
            stock=20,
            category_id=sample_category.id
        )
        product = service.create(obj_in)
        assert product.slug == "samsung-galaxy-s25-fe"
        assert product.id is not None

    def test_create_product_persists_to_db(self, db_session, sample_category):
        service = ProductService(db_session)
        from app.schemas.product_schema import ProductCreate
        obj_in = ProductCreate(
            name="Test Product",
            price=10.00,
            stock=5,
            category_id=sample_category.id
        )
        product = service.create(obj_in)
        fetched = service.get_by_id(product.id)
        assert fetched is not None
        assert fetched.name == "Test Product"


class TestProductImages:

    def test_add_image_success(self, db_session, sample_products):
        service = ProductService(db_session)
        product = sample_products[0]
        image = service.add_image(product_id=product.id, image_url="http://example.com/img.jpg")
        assert image.id is not None
        assert image.image_url == "http://example.com/img.jpg"
        assert image.is_primary is False

    def test_add_image_as_primary(self, db_session, sample_products):
        service = ProductService(db_session)
        product = sample_products[0]
        image = service.add_image(product_id=product.id, image_url="http://example.com/main.jpg", is_primary=True)
        assert image.is_primary is True


class TestSlugGeneration:

    def test_generate_slug_with_special_characters(self, db_session):
        service = ProductService(db_session)
        slug = service._generate_slug("Samsung Galaxy S24+ (5G)!!")
        assert slug == "samsung-galaxy-s24-5g"

    def test_generate_slug_with_multiple_spaces(self, db_session):
        service = ProductService(db_session)
        slug = service._generate_slug("  Product   With    Spaces  ")
        assert slug == "product-with-spaces"        
    def test_generate_slug_with_only_special_characters(self, db_session):
        service = ProductService(db_session)
        slug = service._generate_slug("!!!@@@###")
        assert slug == ""