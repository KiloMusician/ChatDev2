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

   conda create -n ChatDev_conda_env python=3.9 -y
   conda activate ChatDev_conda_env

      cd ChatDev
   pip3 install -r requirements.txt

      export OPENAI_API_KEY="your_OpenAI_API_key"

         python3 run.py --task "[description_of_your_idea]" --name "[project_name]"

         6. **Run Your Software:** Once generated, you can find your software in the `WareHouse` directory under a specific
   project folder, such as `project_name_DefaultOrganization_timestamp`. Run your software using the following command
   within that directory:
   On Unix/Linux:
   ```
   cd WareHouse/project_name_DefaultOrganization_timestamp
   python3 main.py


- here is the full params of run.py

    ```commandline
    usage: run.py [-h] [--config CONFIG] [--org ORG] [--task TASK] [--name NAME] [--model MODEL]

    argparse

    optional arguments:
      -h, --help       show this help message and exit
      --config CONFIG  Name of config, which is used to load configuration under CompanyConfig/; Please see CompanyConfig Section below
      --org ORG        Name of organization, your software will be generated in WareHouse/name_org_timestamp
      --task TASK      Prompt of your idea
      --name NAME      Name of software, your software will be generated in WareHouse/name_org_timestamp
      --model MODEL    GPT Model, choose from {'GPT_3_5_TURBO','GPT_4','GPT_4_32K'}
    ```


- the generated software is under ``WareHouse/NAME_ORG_timestamp``, including:
    - all the files and manuals of this software
    - config files of company which made this software, including three config json files
    - full log of the software building process
    - prompt to make this software
- A case of todo software is just like below, which is located in ``/WareHouse/todo_THUNLP_20230822165503``
    ```
    .
    ├── 20230822165503.log # log file
    ├── ChatChainConfig.json # Configuration
    ├── PhaseConfig.json # Configuration
    ├── RoleConfig.json # Configuration
    ├── todo.prompt # User query prompt
    ├── meta.txt # Software building meta information
    ├── main.py # Generated Software Files
    ├── manual.md # Generated Software Files
    ├── todo_app.py # Generated Software Files
    ├── task.py # Generated Software Files
    └── requirements.txt # Generated Software Files
    ```
- Usually you just need to install requirements and run main.py to use your software
    ```commandline
    cd WareHouse/project_name_DefaultOrganization_timestamp
    pip3 install -r requirements.txt
    python3 main.py
    ```

## Local Demo

- you can start a flask app first to get a local demo, including enhanced visualized logs, replay demo, and a simple
  ChatChain Visualizer.

```
python3 online_log/app.py
```

then go to [Local Demo Website](http://127.0.0.1:8000/) to see an online visualized version of logs such as

![demo](misc/demo.png)

- You can also goto the [ChatChain Visualizer](http://127.0.0.1:8000/static/chain_visualizer.html) on this page and
  upload any ``ChatChainConfig.json`` under ``CompanyConfig/`` to get a visualization on this chain, such as:

![ChatChain Visualizer](misc/chatchain_vis.png)

- You can also goto the Chat Replay page to replay log file in the software folder
    - click the ``File Upload`` bottom to upload a log, then click ``Replay``
    - The replay only shows the dialogues in natural languages between agents, it will not contain debug logs.

![Replay](misc/replay.gif)

