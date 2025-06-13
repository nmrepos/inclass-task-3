# INFO8985_monolith
otel for a python monolithic app

## SigNoz Setup

This project can export traces, metrics and logs directly to [SigNoz](https://github.com/SigNoz/signoz).
Clone the SigNoz repo as a submodule and start its Docker compose stack:

```bash
git submodule add https://github.com/SigNoz/signoz.git signoz
cd signoz/deploy/docker/clickhouse-setup
docker compose up -d
cd ../../..
```

If the repository was cloned without submodules, initialise them with:

```bash
git submodule update --init --recursive
```

The application expects the OTLP endpoint to be available at `http://localhost:4317`.
Exporters will read this from the `OTEL_EXPORTER_OTLP_ENDPOINT` environment variable.

```bash
ansible-playbook up.yml
```

This is based on [the open telemetry docs](https://opentelemetry.io/docs/languages/python/getting-started/)

Run the OpenTelemetry collector and SigNoz stack using `docker compose up -d`. In another terminal window start the application:

```bash
export OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED=true
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
opentelemetry-instrument --logs_exporter otlp flask run -p 8080
```
or for tracing, metric monitoring and logging


```bash
export OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED=true
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
opentelemetry-instrument --logs_exporter otlp --metrics_exporter otlp --traces_exporter otlp --service_name dice-service flask run -p 8081
```

```bash
opentelemetry-instrument python app.py
```



# REPORT

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
