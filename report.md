#### **1) Log, trace, and collect metrics in SigNoz**

  * Flask app sends traces (`roll` span).
  * logs appear in SigNoz (`testuser is rolling the dice: 4`).
  * custom metric (`dice_rolls`) appears in SigNoz.


#### **2) Add an exception to the roll function and get the exception into SigNoz**


    ```python
    def roll():
        result = randint(1, 6)
        if result == 6:
            raise RuntimeError("something broke while rolling the dice")
        return result
    ```
  * When  hit `/rolldice` enough times, it will raise an exception 

#### **3) Make sure the application doesn't "swallow" the exception**

    ```python
    except Exception:
        logger.exception("roll failed")
        raise
    ```
  * The exception is re-raised, so Flask returns an error and you see the error both in the logs and in traces.
