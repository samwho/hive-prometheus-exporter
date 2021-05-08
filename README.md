# hive-prometheus-exporter

This project is a Docker image that polls [Hive Home's][1] API and exposes
metrics about your smart devices. The metrics are exposed through the
[Prometheus][2] client, so you'll need a Prometheus installation to collect
them.

## Usage

The Docker image requires a few environment variables to work properly. Fill in
the following and save it to a file called `.env`:

```env
PORT=8888
HIVE_USERNAME=
HIVE_PASSWORD=
POLLING_INTERVAL_SECONDS=60
LOG_LEVEL=INFO
```

Then you can run:

```bash
docker run --env-file .env -p 8888:8888 samwho/hive-prometheus-exporter
```

And if you navigate to `http://localhost:8888` in your browser, you should see
a bunch of Prometheus metrics. Anything starting with `hive_` is a metric that
has been exported by this project.

[1]: https://www.hivehome.com/
[2]: https://prometheus.io/
