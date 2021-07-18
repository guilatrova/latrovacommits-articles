# How to structure exception in Python like a PRO 🐍 🏗️ 💣

Given now you know how to properly [handle your exceptions](https://blog.guilatrova.dev/handling-exceptions-in-python-like-a-pro/) with [Tryceratops 🦖](https://blog.guilatrova.dev/project-tryceratops/) help, the next step is to structure them effectivelly so you can scale and reuse.

## What exceptions should represent?

To make it short: *"SOMETHING EXPECTED happen"*.

You frequently **don't care about precision, but accuracy**. It means that you don't need to know exactly WHY something failed (e.g. bad internet connection? provider is off?), but you should focus on **WHAT failed so you can respond to**.

I'll start sharing a real-life example. Let me explain the boring bussiness part quick: Back when I worked at [Mimic](https://latamlist.com/2019/12/15/brazilian-food-delivery-startup-mimic-receives-9m-seed-round/) we used a third-party API named [Onfleet](https://onfleet.com/) to assign orders to couriers. At that time we decided to break it down into two steps:

1. Create a pick-up task (courier taking the order),
2. Create a drop-off task (courier takes the order to the customer).

Different API calls are made, and the latter depends on the first. Anything might go wrong, and if it does we need to **UNDO** anything we've done previously.

Focus on having:

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
```

Rather:

```py
```

## When to create?

## How to structure them

## Real-life examples

## Extending and categorizing

## Where to keep them
