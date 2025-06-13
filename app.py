# These are the necessary import declarations
import os
from opentelemetry import trace, metrics, logs
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk.trace.export import BatchSpanProcessor, OTLPSpanExporter
from opentelemetry.sdk.metrics.export import (
    PeriodicExportingMetricReader,
    OTLPMetricExporter,
)
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor, OTLPLogExporter

from random import randint
from flask import Flask, request
import logging

# Setup OpenTelemetry providers and exporters for SigNoz
resource = Resource(attributes={SERVICE_NAME: "dice-service"})

trace_provider = TracerProvider(resource=resource)
span_exporter = OTLPSpanExporter(
    endpoint=os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"),
    insecure=True,
)
trace_provider.add_span_processor(BatchSpanProcessor(span_exporter))
trace.set_tracer_provider(trace_provider)

metric_exporter = OTLPMetricExporter(
    endpoint=os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"),
    insecure=True,
)
metric_reader = PeriodicExportingMetricReader(metric_exporter)
meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
metrics.set_meter_provider(meter_provider)

log_exporter = OTLPLogExporter(
    endpoint=os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"),
    insecure=True,
)
log_provider = LoggerProvider(resource=resource)
log_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))
logs.set_logger_provider(log_provider)
logging.getLogger().addHandler(
    LoggingHandler(level=logging.INFO, logger_provider=log_provider)
)

# Acquire a tracer
tracer = trace.get_tracer("diceroller.tracer")
# Acquire a meter.
meter = metrics.get_meter("diceroller.meter")

# Now create a counter instrument to make measurements with
roll_counter = meter.create_counter(
    "dice.rolls",
    description="The number of rolls by roll value",
)

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route("/rolldice")
def roll_dice():
    # This creates a new span that's the child of the current one
    with tracer.start_as_current_span("roll") as roll_span:
        player = request.args.get('player', default = None, type = str)
        try:
            result = str(roll())
        except Exception:
            logger.exception("roll failed")
            raise
        roll_span.set_attribute("roll.value", result)
        # This adds 1 to the counter for the given roll value
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
