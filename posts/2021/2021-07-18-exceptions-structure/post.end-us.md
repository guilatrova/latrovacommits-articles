# How to structure exception in Python like a PRO 🐍 🏗️ 💣

Given now you know how to properly [handle your exceptions](https://blog.guilatrova.dev/handling-exceptions-in-python-like-a-pro/) with [Tryceratops 🦖](https://blog.guilatrova.dev/project-tryceratops/) help, the next step is to structure them effectivelly so you can scale and reuse.

## What exceptions should represent?

To make it short, exceptions represent: *"SOMETHING EXPECTED happened"*.

You frequently **don't care about precision, but accuracy**. It means that you don't need to know exactly WHY something failed (e.g. bad internet connection? provider is off?), but you should focus on **WHAT failed so you can respond to**.

I'll start sharing a real-life example. Let me explain the boring bussiness part quick: Back when I worked at [Mimic](https://latamlist.com/2019/12/15/brazilian-food-delivery-startup-mimic-receives-9m-seed-round/) we used a third-party API named [Onfleet](https://onfleet.com/) to assign orders to couriers. At that time we decided to break it down into two steps:

1. Create a pick-up task (courier taking the order),
2. Create a drop-off task (courier takes the order to the customer).

Different API calls are made, and the latter depends on the first. Anything might go wrong, and if it does we need to **UNDO** anything we've done previously.

Please note the **straight flow from top to bottom**. That's the success path (`try` and `else` block) that may raise exceptions.

Next, consider the **left to right flow**. That's the exception handling path (`except` blocks) that also can raise exceptions.

![Courier assignment flow with exceptions](assignment-flow-handler.png)

The production code for this function is exactly as follows:

```py
# Good sample
class OnfleetService:
    def create_tasks(self, order: Order) -> dict:
        try:
            self._prevent_tasks_duplicities(order.id)
            pick_up_task = self._create_pick_up_task(order)
            drop_off_task = self._create_drop_off_task(order, pick_up_task)
        except exceptions.StorePickUpTaskFailed as error:
            self._delete_task(error.pick_up_task_id)
            raise
        except exceptions.CreateDropOffTaskFailed:
            self._delete_task(pick_up_task.id)
            raise
        except exceptions.StoreDropOffTaskFailed as error:
            self._delete_task(pick_up_task.id)
            self._delete_task(error.drop_off_task_id)
            raise
        else:
            logger.info("Tasks were created and stored successfully")

            return {
                "pick_up_task": pick_up_task,
                "drop_off_task": drop_off_task,
            }


def handle_incoming_orders(orders: Iterable[Order]):
    for order in orders:
        try:
            logger.debug(f"Received order: {order}")
            onfleet_service.create_tasks(order)
        except exceptions.TasksAlreadyExists:
            pass
```

Note how **we focus on the "WHAT":** `StorePickupTaskFailed`, `CreateDropOffTaskFailed`, `StoreDropOffTaskFailed`.
We (and you shouldn't either) don't care whether the function failed because of bad `json` syntax, or their API replied with 400, or the database was unavailable at the moment, or an invalid foreign key issue happened. **All this information will be contained and logged in the strack trace already!**

Instead, my code must REACT to WHAT happens:

- If I can't save the pick up task in my database (for any reason), I need to send a `DELETE` request to remove it from the third-party (otherwise they have a task that our microservice doesn't know about);
- If I can't create the drop off task on their API (for any reason), I need to repeat the same flow above;
- If I can't save the drop off task in my database (for any reason), I need to repeat the same flow above + send another `DELETE` request to remove the drop off as well;

For all the cases we `raise` again because this service layer is not responsible for logging, alarming, or presenting the user a better UI, it's just responsible for mitigating risks to the operation (e.g. Prevent couriers from picking an order without a drop off, or trigerring events we're never able to forward to the end user like: "the courier is on its way to deliver your order").

It would be hard and probably useless to have very specific exceptions (precision):

```py
# Bad sample
class OnfleetService:
    def create_tasks(self, order: Order) -> dict:
        try:
            self._prevent_tasks_duplicities(order.id)
            pick_up_task = self._create_pick_up_task(order)
            drop_off_task = self._create_drop_off_task(order, pick_up_task)
        except (
            exceptions.StorePickupFailedDueDatabaseUnavailable,
            exceptions.StorePickupFailedDueBadForeignKey,
            exceptions.StorePickupFailed,
            exceptions.StorePickupFailedUnknownReason,
        ) as error:
            self._delete_task(error.pick_up_task_id)
            raise
        except (
            exceptions.CreateDropOffTaskBadSyntax,
            exceptions.CreateDropOffTaskMissingProp,
            exceptions.CreateDropOffTaskValidation,
            exceptions.CreateDropOffTaskFailedUnknown
        ):
            self._delete_task(pick_up_task.id)
            raise

        ...
```

##



## When to create?

## How to structure them

## Real-life examples

## Extending and categorizing

## Where to keep them
