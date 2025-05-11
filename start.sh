rcc run -t repos -e devdata/env-for-producer.json
rm -rf output/*
rcc run -t producer -e devdata/env-for-producer.json
rm -rf output/*
rcc run -t consumer -e devdata/env-for-consumer.json