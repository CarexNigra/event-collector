# event-collector  

### Build and run  

To activate certain python `.venv` in vscode (to make code highlighting work) - add interpreter path starting from the project's root, like that:  
```shell
./api/.venv/bin/python
```  

*TODO:*



### How to set up kafka producer locally
0. Run docker
* Create docker-compose.yml (example: https://github.com/confluentinc/cp-all-in-one/blob/7.6.1-post/cp-all-in-one-kraft/docker-compose.yml)
* in terminal go to the folder with this file and run following command to create a container: docker-compose up -d
* (to close: docker-compose down)
 
1. Create kafka topic manually
* In terminal: docker ps 
* in the output get docker id (first sting)
* go to docker: docker exec -it <docker_id> bash
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
curl -v -X POST -H "Content-Type: application/json" 'http://localhost:5000/store' -d '{"event_name": "TestEvent", "context": {"sent_at": 1701530942, "received_at": 1701530942, "processed_at": 1701530942, "message_id": "36eca638-4c0f-4d11-bc9b-cc2290851032", "user_agent": "some_user_agent"}, "data": {"user_id": "example_user_id", "account_id": "example_account_id", "user_role": "OWNER"}}'
```  

4. Check that event ends up in the consumer logs
* In the terminal with kafka-console-consume (see in 2. above) there will be a message we just sent printed out
* In the terminal with the app running, there will be following message printed out '127.0.0.1:51296 - "POST /store HTTP/1.1" 204 No Content'

# How to set up path to config file
* Define environment name in terminal as follows: os.environ["ENVIRONMENT"] = <env_var_string>
* <env_var_string> can be either "dev", or "stage", or "prod"
* this value will be passed to `environmnet_type` variable of `get_config_path` function and used to construct path to config file

# How to run the full service locally (when everything is already set up)
0. Run docker
* In terminal go to the folder with `docker-compose.yml` file (in our case ../local)
* Run following command to create a container: `docker-compose up -d`

1. View consumed kafka messages using following setup;
* Open another terminal session
* Run `docker ps`
* In the output get `broker` docker container_id (first sting)
* go to the docker container: `docker exec -it <container_id> bash`
* [if not known] find kafka-topic file on broker: `ls -ls /bin/ | grep kafka-console-consumer` # In our case its name is `kafka-console-consumer`
* using kafka-topic file name, run: `kafka-console-consumer --bootstrap-server localhost:9092 --topic event-messages --from-beginning`
* There will be a message printed here, after we run 2.

2. Launch api server and send test request with an event to it
* Open another terminal session
* Go to the folder where Makefile is located (root): `make run.api`
* Open yet another terminal session, send test event to api
```shell
curl -v -X POST -H "Content-Type: application/json" 'http://localhost:5000/store' -d '{"event_name": "TestEvent", "context": {"sent_at": 1701530942, "received_at": 1701530942, "processed_at": 1701530942, "message_id": "36eca638-4c0f-4d11-bc9b-cc2290851032", "user_agent": "some_user_agent"}, "data": {"user_id": "example_user_id", "account_id": "example_account_id", "user_role": "OWNER"}}'
```  

3. Check that event ends up in the consumer logs
* In the terminal with kafka-console-consumer (see in 2. above) there will be a message we just sent printed out
* In the terminal with the app running, there will be following message printed out `127.0.0.1:51296 - "POST /store HTTP/1.1" 204 No Content`


# NOTES
1. Sometimes we need to re-create .venv. For example, if you restructure project and move files and folders around. For this you should only run `make install`
2. See the content of temp file `ls -la /tmp/`


# TO SET UP CREDENTIALS FOR MINIO 
1. Open your .zshrc file:
```
nano ~/.zshrc
```
2. Add MinIO credentials:
```
export MINIO_ACCESS_KEY="minio_user"
export MINIO_SECRET_KEY="minio_password"
```
3. Save and exit: If you're using nano, press CTRL + X, then Y to confirm, and press Enter to save.
4. Apply the changes by sourcing the file or restarting your terminal
```
source ~/.zshrc
```

# TODO
1. 3 brockers and zookeeper
2. Each event – write to new line
2. Avoid reading to get file size. Use storage methods
2. Checks with ruff
3. CI/CD: github workflow: checks and tests
4. Prometheus metrics
– for producer
– for consumer
5. Readme
6. Miro board with service map
7. Blog post