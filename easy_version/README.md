# FundLoadRestrictions assesment repository
In the financial services industry, it's critical to manage the flow of funds into customer accounts while adhering to specific velocity limits and other controls

# How to start:
1. Create a virtual environment
2. Activate the virtual environment
3. Install requirements.txt file using ´pip install -r requirements.txt´
4. Run ´python plain.py´ in terminal / command prompt
5. Incoming data should be stored in input.txt file
6. Output will be stored in output.txt file

# How to test:
Run ´pytest -m gptests´ in terminal / command prompt

# Architecture:
## General suggestions through creation: designed and architected as "easy, short and testable".
- plain.py is the single script that reads incoming data from input.txt file and writes calculated results to output.txt file.

- The script contains following parts:
    1. Storage Searching functions: help to organize and process incoming data in memory-storage
    2. cleaning function transfer incoming data in python object (serializer)
    3. validators: different functions, every implemented one rule from business-rules list
    4. "is_valid" Business logic function, performs check of all business rules for every entity of incoming data.
    5. response generator function: generates response message according to result of validation (output serializer)
    6. helper functions to organize all work

-  plain.py Code is self-explanatory, but contains comments for each part of the script and some general comments. Additional documentation is not provided, except readme and assessment remarks.

- gptests.py contains test cases for function in plain.py script


# Settings:
- every limits can be changed in `LIMITS` dictionary on the top of plain.py script
- daily multipliers for loading amounts can be changed in `DIVIDER_PER_DAY` dictionary on the top of plain.py script
- business rules pipleline can be changed in business_rules list in `is_valid` function

# Maintainability, extensibility, and scalability
- system can not be scaled through parallelization/workers or distributed computing because base data is stored in memory. But it can be easily modified to use other storage solutions.

- Base settings for business process can be easily changed through modification of `LIMITS` and `DIVIDER_PER_DAY` dictionaries.

- script can be easily extended to add new business rules, without changing existing ones.

- business process in script can be changed through modification of `is_valid` function.
- Incoming data cleaning can be changed through modification of `clean` function.
- Outgoing data can be changed through modification of `prepare_response` function

- system can be extended by adding new business rules, without changing existing ones

- Performance can be increased by changing standard Json to orJson library, or PyPy can be used instead of CPython interpreter.

- Current code stage can be easily tested by running pytest -m gptests. Tests coverage of last version plain.py is 99.9% (coverage run -m gptests)


# conventions and assumptions
1. are strictly defined the input.txt and output.txt
2. input data is always valid
3. There are multiple entities with same id (load id) not existed in input.txt
4. Not valid loads are ignored during calculation
6. id prime check function uses sympy.ntheory.isprime function.
5. Any exceptions during processing not handled, except validation errors (used in processing pipeline), accordingly to assessment remark : "Extensive error handling is not necessary"
7. Whole script is written in python as a plain tny and short code with reduced complexity , accordingly to assessment remark : "Do not over-design ..."

# Comments:
1. Enterprize version of this solution with additional features can be found in https://github.com/danilovmy/FundLoadRestrictions folder, it builded on Django framework and offers API-interface for user interaction. It not polished yet, but it works.

2. Creation of Plain version of this solution takes about 6 hours, including tests development. Although Enterprize version was created in less than 3 hours. https://github.com/danilovmy/FundLoadRestrictions/tree/main/easy_version

3. On start i use LLms, examples of prompts can be found in repository, but after one hour of work i "hit my plan usage limits and should Upgrade Agent Plan to continue" thats why this solution was created without LLMs usage.
