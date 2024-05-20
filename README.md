# eventhub  

### Build and run  

To activate certain python `.venv` in vscode (to make code highlighting work) - add interpreter path starting from the project's root, like that:  
```shell
./api/.venv/bin/python
```  

*TODO:*



### How to run kafka producer locally

1. Create kafka topic manually
* In terminal: docker ps 
* in the output get docker id (first sting)
* go docker: docker exec -it <docker_id> bash
* find kafka-topic file on brocker: ls -ls /bin/ | grep kafka-topics
* create topic in the file: kafka-topics --bootstrap-server localhost:9092 --create --topic event-messages --partitions 3
* list all topics: kafka-topics --bootstrap-server localhost:9092 --list
* since topics are removed after we stop the docker, we need to encode it in docker-compose.yaml with the number of partitions and replicas. This is done by spinning an additional container init-kafka that runs a defined script (see docker-compose.yaml)


2. Create a simple kafka consumer in docker (we need to see all messages sent to kafka somewhere. The easiest way is to create a consumer with printing function)
* As an alternative it was decided to view kafka messages using following commands
* In terminal: docker ps 
* in the output get docker id (first sting)
* go docker: docker exec -it <docker_id> bash
* find kafka-topic file on brocker: ls -ls /bin/ | grep kafka-console-consumer
* run: kafka-console-consumer --bootstrap-server localhost:9092 --topic event-messages --from-beginning
* There will be a message printed here, after we run 3.


3. Launch api server and send test request with an event to it
* go to api folder (where Makefile is located): make run
* go to the separate terminal, send test event to api
```shell
curl -v -X POST -H "Content-Type: application/json" 'http://localhost:8000/store' -d '{"event_name": "TestEvent", "context": {"sent_at": 1701530942, "received_at": 1701530942, "processed_at": 1701530942, "message_id": "36eca638-4c0f-4d11-bc9b-cc2290851032", "user_agent": "some_user_agent"}, "data": {"user_id": "example_user_id", "account_id": "example_account_id", "user_role": "OWNER"}}'
```  

4. Check that event ends up in the consumer logs
* In the terminal with kafka-console-consume (see in 2. above) there will be a message we just sent printed out
* In the terminal with the app running, there will be following message printed out '127.0.0.1:51296 - "POST /store HTTP/1.1" 204 No Content'