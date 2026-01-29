./app
  - workflows
    - business_workflow.py # this is the workflow definition, which will orchestrate the activities< but notice , it will only import the sdk/contracts.py to get the dto define, and call the gateway.py to execute the activities, but it can not directly import the gateway.py activity function define but only the contracts.py, so contracts.py is the only way to communicate between workflow and activity , which means we need a way to bind the activity function define to the contracts with temporal, *notice dont import the gateway.py directly!! never ever!!
  - domains
    - hello
      - sdk/
        - __init__.py
        - contracts.py #  include dto define , use pydantic , which make workflow can safely orchestration the activities
      - gateway.py # activity define ,which will wrapped as temporal activity, inside will call usercases.py
      - models.py # domain entity define
      - infrastructure.py # implement the the repository interface , which will work as Anti-Corruption Layer. interact with database or others, but since the project will become bigger ,so it is nessary to orginze the infrastructure into sub-folders, each sub-folder will contain the repository interface implementation and the database or others interact code like db, s3 etc
      - services.py # pure interface define, make sure the services will only define what they want to implement, they just need to define the interface, no implementation here.
      - usecases.py # pure business logic define, will import the services.py interface define, pure python logic here no other outside system needed like db ,s3 interact etc.
    - pizza
      ... # same structure as upper
    - user
      ... # same structure as upper
  - infrastructure # some common infrastructure, but make sure they dont directly import the domain module, you need to think a Dependency Inversion way to solve the domain infrastructure to interact with the global infrastructure system without violate the domain module's boundary
    - workflows/
      - worker.py # reference app/worker/main.py in old project , this will give the ability to run the workflow and activity
      - temporal_client.py # temporal client define
    - s3/
      - s3_client.py # s3 client define
      - s3_repository.py # s3 repository implementat