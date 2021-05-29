# flake8: noqa

### Services

class StatusService:
    def get_order_status(order_id):
        try:
            ...
        except Exception as e:
            raise OrderNotFound(order_id) from e


class ReceiptService:
    def create(order_id):
        try:
            ...
        except Exception as e:
            raise ReceiptGenerationFailed(order_id) from e


class Broker:
    def emit_receipt_note(receipt_note):
        try:
            ...
        except Exception as e:
            raise ReceiptEmissionFailed(order_id) from e

### Main class

class OrderService:
    def emit(self, order_id: str) -> dict:
        try:
            order_status = status_service.get_order_status(order_id)

            (
                is_order_locked_in_emission,
                seconds_in_emission,
            ) = status_service.is_order_locked_in_emission(order_id)
            if is_order_locked_in_emission:
                logger.info(
                    "Redoing emission because "
                    "it was locked in that state after a long time! "
                    f"Time spent in that state: {seconds_in_emission} seconds "
                    f"Order: {order_id}, "
                    f"order_status: {order_status.value}"
                )

            elif order_status == OrderStatus.EMISSION_IN_PROGRESS:
                logger.info("Aborting emission request because it is already in progress!")
                return {"order_id": order_id, "order_status": order_status.value}

            elif order_status == OrderStatus.EMISSION_SUCCESSFUL:
                logger.info(
                    "Aborting emission because it already happened! "
                    f"Order: {order_id}, "
                    f"order_status: {order_status.value}"
                )
                return {"order_id": order_id, "order_status": order_status.value}

            receipt_note = receipt_service.create(order_id)
            broker.emit_receipt_note(receipt_note)
            order_status = status_service.get_order_status(order_id)
        except OrderNotFound as e:
            logger.exception(
                f"Order {order_id} was not found in db "
                f"to emit. Error: {e}."
            )
            raise
        except ReceiptGenerationFailed as e:
            logger.exception(
                "Error found during emission! "
                f"Order: {order_id}, "
                f"exception: {e}"
            )
            raise
        except ReceiptEmissionFailed as e:
            logger.exception(
                "Emission failed! "
                f"Order: {order_id}, "
                f"exception: {e}"
            )
            raise
        else:
            return {"order_id": order_id, "order_status": order_status.value}
