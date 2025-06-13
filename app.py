import os
from random import randint
from flask import Flask, request
import logging

from opentelemetry import trace, metrics
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter

# --- OpenTelemetry Setup ---

resource = Resource(attributes={SERVICE_NAME: "dice-service"})

# Tracing
trace_provider = TracerProvider(resource=resource)
span_exporter = OTLPSpanExporter(
    endpoint=os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318/v1/traces"),  # SigNoz default OTLP HTTP port
)
trace_provider.add_span_processor(BatchSpanProcessor(span_exporter))
trace.set_tracer_provider(trace_provider)

# Metrics
metric_exporter = OTLPMetricExporter(
    endpoint=os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318/v1/metrics"),
)
metric_reader = PeriodicExportingMetricReader(metric_exporter)
meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
metrics.set_meter_provider(meter_provider)

# --- Flask App and Business Logic ---

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

tracer = trace.get_tracer("diceroller.tracer")
meter = metrics.get_meter("diceroller.meter")

roll_counter = meter.create_counter(
    "dice.rolls",
    description="The number of rolls by roll value",
)

@app.route("/rolldice")
def roll_dice():
    with tracer.start_as_current_span("roll") as roll_span:
        player = request.args.get('player', default=None, type=str)
        try:
            result = str(roll())
        except Exception:
            logger.exception("roll failed")
            raise
        roll_span.set_attribute("roll.value", result)
        roll_counter.add(1, {"roll.value": result})
        if player:
            logger.warning("%s is rolling the dice: %s", player, result)
        else:
            logger.warning("Anonymous player is rolling the dice: %s", result)
        return result

def roll():
    result = randint(1, 6)
    if result == 6:
        raise RuntimeError("something broke while rolling the dice")
    return result

if __name__ == "__main__":
    app.run(port=8081)
