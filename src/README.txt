Presequisites:
 - python version 3.10 (or greater)
 - pyspark installation (https://spark.apache.org/docs/latest/api/python/getting_started/install.html)
 - numpy installation (https://numpy.org/install/)
 - matplotlib (https://matplotlib.org/stable/users/installing/index.html)
 - python-dotenv (https://pypi.org/project/python-dotenv/)

The installation of matplotlib is necessary only if you want to run the tests on the data.

----------------------------------------------------------------------------------------------------------------------------------------------

To run all the three points without the data generation, it is necessary to do the following steps:
 - copy in the same location of the "src" folder the "data" folder (input data)
 - set the "RUN_ID" parameter in the .env file with the same value appended to the json files
	(example: if "standard1.json" and "actual1.json" are the names of the files for the data in input, RUN_ID=1 should be set)

After this two steps, it is enough to run the command:

	py src/main.py

outside the src folder.

Instead, if the data generation is wanted, the parameters in the .env file can be changed to shape the routes.
The data will be generated and put in the "data" folder, while the outputs in the "output" folder.
On all this files the RUN_ID specified in the .env will be appended.

The same passages described above are valid if it is wanted to run only one step at a time.
The three commands are:

	py src/first_main.py
	py src/second_main.py
	py src/third_main.py


With the same logic, the tests can be runned, using the following commands:

	py src/test/first_test.py
	py src/test/second_test.py
	py src/test/third_test.py
