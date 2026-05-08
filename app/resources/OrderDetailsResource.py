from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field

from .AbstractBaseResource import AbstractBaseResource
from ..services.MySQLDataService import MySQLDataService


class OrderDetail(BaseModel):
    orderNumber: int
    productCode: str
    quantityOrdered: int
    priceEach: Decimal
    orderLineNumber: int


class OrderDetailsCollection(BaseModel):
    items: list[OrderDetail] = Field(default_factory=list)


class OrderDetailsResource(AbstractBaseResource):
    def __init__(self, config: dict | None = None) -> None:
        cfg = dict(config or {})
        super().__init__(cfg)

        service_config = {
            "table_name": "orderdetails",
            "primary_key_field": "orderNumber",
        }

        self._service = MySQLDataService(service_config)

    def get(self, template: dict) -> OrderDetailsCollection:
        rows = self._service.retrieveByTemplate(template)
        return OrderDetailsCollection(
            items=[OrderDetail.model_validate(row) for row in rows]
        )

    def get_by_id(self, id: str) -> OrderDetailsCollection:
        rows = self._service.retrieveByTemplate({"orderNumber": int(id)})
        if not rows:
            raise ValueError(f"No order details with orderNumber {id!r}")

        return OrderDetailsCollection(
            items=[OrderDetail.model_validate(row) for row in rows]
        )

    def get_by_order_and_product(self, orderNumber: str, productCode: str) -> OrderDetail:
        rows = self._service.retrieveByTemplate(
            {
                "orderNumber": int(orderNumber),
                "productCode": productCode,
            }
        )

        if not rows:
            raise ValueError(
                f"No order detail with orderNumber {orderNumber!r} and productCode {productCode!r}"
            )

        return OrderDetail.model_validate(rows[0])

    def post(self, new_data: OrderDetail) -> str:
        data = new_data.model_dump()
        self._service.create(data)
        return f"{data['orderNumber']}-{data['productCode']}"

    def delete(self, id: str) -> int:
        return self._service.deleteByPrimaryKey(str(id))

    def delete_by_order_and_product(self, orderNumber: str, productCode: str) -> int:
        return self._service.deleteByTemplate(
            {
                "orderNumber": int(orderNumber),
                "productCode": productCode,
            }
        )

    def put(self, orderNumber: str, new_data: OrderDetail) -> int:
        data = new_data.model_dump()
        data["orderNumber"] = int(orderNumber)
        return self._service.updateByPrimaryKey(str(orderNumber), data)

    def put_by_order_and_product(
        self,
        orderNumber: str,
        productCode: str,
        new_data: OrderDetail,
    ) -> int:
        data = new_data.model_dump()
        data["orderNumber"] = int(orderNumber)
        data["productCode"] = productCode

        return self._service.updateByTemplate(
            {
                "orderNumber": int(orderNumber),
                "productCode": productCode,
            },
            data,
        )