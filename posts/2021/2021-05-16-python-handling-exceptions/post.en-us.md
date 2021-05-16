# Handling exceptions in Python like a pro 🐍 💣

One of the downsides of a flexible language like python is that people often assume that as long as something works then it's probably the proper way of doing so. I would like to write this humble guide on how to use effectively use python exceptions and how to handle exceptions and log them correctly.

## Handling exceptions effectively

### Intro

Let's consider the following system, a microservice responsible for:

- Listening to new order events;
- Producing a receipt;
- Printing the receipt;
- Storing the receipt in the database;
- Sending receipts to the Internal Revenue System (IRS);

Anything can break at any moment. You might have trouble with the order object missing important information, or maybe your printer is out of paper, maybe the IRS is out of service and you can't sync the receipt with them, or maybe, who know, your database is unavaiable at the moment.

You must respond to any situation properly and proactively to mitigate errors when handling new orders.

And this is the actual kind of code (which althought works, it's wrong and ineffective) that I see people writing:

```py
class OrderService:
    def emit(self, order_id: str) -> dict:

        try:
            order_status = status_service.get_order_status(order_id)
        except Exception as e:
            logger.exception(
                f"Order {order_id} was not found in db "
                f"to emit. Error: {e}."
            )
            raise e

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

        try:
            receipt_note = receipt_service.create(order_id)
        except Exception as e:
            logger.exception(
                "Error found during emission! "
                f"Order: {order_id}, "
                f"exception: {e}"
            )
            raise e

        try:
            broker.emit_receipt_note(receipt_note)
        except Exception as e:
            logger.exception(
                "Emission failed! "
                f"Order: {order_id}, "
                f"exception: {e}"
            )
            raise e

        order_status = status_service.get_order_status(order_id)
        return {"order_id": order_id, "order_status": order_status.value}
```

I'll focus first on `OrderService` excessive knowledge which makes him somewhat a [Blob](https://sourcemaking.com/antipatterns/the-blob) and later on I will explore proper reraising + proper exception logging.

### Why is this service a blob

This service knows too much. Some people may argue that this service only knows about what it should know (i.e. all steps related to receipt generation), but it knows way more than that.

It focuses on producing errors (e.g. database, printing, order status) instead of what it does (e.g. retrieve, check status, generate, send) and how to respond in case of failures.

In that sense, it makes me feel that the client is teaching the serving class what exceptions it might produce. If we decide to reuse it in any other step  (let's say a customer wants another printed copy from an older order receipt), we would be replicating most of this code.

Although this service works fine, it's hard to maintain, and it's not clear how one step correlates to the other due the repeated `except` blocks between every step which take away our attention on the "how" to think about "when".

### First improvement: Make exceptions specific

Let's make the exceptions more accurate and specific first.
The benefits can't be seen right away, so I'll not spend too much time explaining it right now. But please, pay attention as the code evolves.

I will only highlight what we modified:

```py
try:
    order_status = status_service.get_order_status(order_id)
except Exception as e:
    logger.exception(...)
    raise OrderNotFound(order_id) from e

...

try:
    ...
except Exception as e:
    logger.exception(...)
    raise ReceiptGenerationFailed(order_id) from e

try:
    broker.emit_receipt_note(receipt_note)
except Exception as e:
    logger.exception(...)
    raise ReceiptEmissionFailed(order_id) from e
```

Note that this time I'm also benefiting of using `from e` which is the correct way of raising an exception from another and keeps the full stack trace.

### Second improvement: Mind your own bussiness

Now that we have custom exceptions, we can move on "don't teaching classes what can go wrong" - they will report to us if it happens!

```py
# Services

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

# Main class

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
```

How does it feel? Much better, right? You have a single `try` block where you can logically follow to understand what happens next, you have grouped specific `except` blocks that helps you understand the "when" situations and edge cases, and lastly you have a `else` block outlining what would happen if everything is successful.

Also, please note that I kept the "reraise" statements `raise` without redeclaring the exception object. It's not a typo. Actually that's the correct way of reraising the current exception: Simple not verbose.

I'm still not happy though. These logs are annoying me.

---

Draft

- Code impl. ()
  - Taxare sample
  - Domain concerns
- Proper declaration of exceptions
  - Effective Python (inherit)
  - Create meaningful messages based on properties + type
- Proper catching
- Proper logging
