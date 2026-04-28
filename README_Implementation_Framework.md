# Implementation Framework — Execution Guide

This package contains the reordered notebook:

- `Implementation_framework_reordered.ipynb`

and should be read together with the server-side benchmark runner used to materialize the MongoDB databases, load the data, and execute the benchmark.

---

## 1) What this workflow does

The full workflow is divided into two major stages:

1. **Methodology stage in the notebook**
2. **Load and benchmark stage on the server through a Python script**

The notebook is responsible for:

1. loading the dataset into DuckDB;
2. registering the raw TSV files for the selected scale factor;
3. building the conceptual views derived from the dataset;
4. defining the conceptual scenario and workload (`QG1`–`QG10`);
5. computing the analytical variables and matrices;
6. inferring the activation classes (`G0`–`G9`);
7. generating the MongoDB configuration catalog;
8. generating the benchmark execution template;
9. exporting the CSV files needed by the external benchmark runner.

The server-side Python runner is responsible for:

1. reading the exported CSV files;
2. materializing each MongoDB experimental configuration;
3. loading the data in batches into MongoDB;
4. creating the required indexes;
5. executing the benchmark queries by query group;
6. exporting raw and aggregated benchmark results.

This separation is intentional: the methodology is computed in the notebook, while the actual MongoDB load and benchmark execution are performed by an external `.py` file on the server.

---

## 2) Repository structure and data source

### Methodology / benchmark repository
Fill in the repository URL here:

- **Framework repository:** `[ADD FRAMEWORK REPOSITORY URL HERE]`

### Dataset repository
The extracted dataset files used by the notebook and by the benchmark pipeline should be available in a separate repository or shared storage location:

- **Dataset repository / storage location:** `https://www.kaggle.com/datasets/nhondangcode/imdb-non-commercial-datasets`

### Scale-factor preparation
The experiments were prepared for the following scale factors:

- `sf0.25`
- `sf0.5`
- `sf1`

The dataset distribution / sampling logic used to produce these scale factors should be documented in a separate file:

- **Scale-factor preparation guide:** `IMDB_SCALE_0_25_0_50_1_SETUP`- File in repository

---

## 3) Data model and exported CSV files

The data loaded into MongoDB was **not** generated from an arbitrary flat-table export. The load is based on a **conceptual modeling step**:

1. the raw dataset is loaded into DuckDB;
2. conceptual views are derived from the source tables;
3. the methodology computes the activated configuration families;
4. the notebook exports CSVs representing the data required by each experiment;
5. the external Python runner materializes MongoDB databases using those exported CSVs.

Therefore, the CSV files used in the MongoDB load are already aligned with the conceptual modeling decisions of the framework.

### Expected extracted files
The benchmark runner expects exported files such as:

- analytical matrix CSV(s);
- configuration catalog CSV(s);
- benchmark execution template CSV;
- entity-level extracted CSVs used for materialization;
- optional pre-materialized CSVs per configuration, when available.


---

## 4) Infrastructure requirements

### DuckDB / notebook environment
Required packages for the methodology notebook:

```bash
pip install pandas numpy duckdb jupyterlab nbformat
```

### MongoDB benchmark environment
Required packages for the server-side benchmark execution:

```bash
pip install pandas numpy pymongo
```

### Optional connectivity tests / external DB connectors
Install only if needed:

```bash
pip install psycopg[binary] cassandra-driver
```

---

## 5) MongoDB infrastructure requirement

To run the load and benchmark stage, you must have a **MongoDB instance available in Docker** so that the experimental databases can be created.

In other words:

- Docker must be installed and running;
- a MongoDB container must already exist and be reachable from the benchmark script;
- the Python benchmark runner will connect to that container and create one database per experiment.

Document your MongoDB container details here:

- **MongoDB container name:** `[ADD CONTAINER NAME HERE]`
- **MongoDB host:** `[ADD HOST HERE]`
- **MongoDB port:** `[ADD PORT HERE]`
- **MongoDB username (if used):** `[ADD USERNAME HERE]`
- **MongoDB password (if used):** `[ADD PASSWORD HANDLING NOTE HERE]`

### Important note
The script does **not** assume that all databases already exist. It creates the experimental databases during materialization. Therefore, the MongoDB container must be active before starting the benchmark script.

---

## 6) Correct execution order

## Part A — Core methodology pipeline in the notebook

Run these blocks in this exact order:

1. **BLOCK 1 — REAL IMDb BUNDLE VIA DUCKDB**
2. **BLOCK 2 — REGISTER THE 7 TSVs OF THE SCALE FACTOR IN DUCKDB**
3. **BLOCK 3 — CONCEPTUAL VIEWS DERIVED FROM IMDb**
4. **INSTANCE 1 — REAL IMDb SCENARIO**
5. **BLOCK V0 — PREPARE THE CONCEPTUAL WORKLOAD**
6. **BLOCK V1 — ORGANIZE THE CONCEPTUAL RELATIONSHIPS**
7. **BLOCK V2 — EXTRACT Rc(Qi) EXACTLY**
8. **BLOCK V3 — INITIAL ROOT CANDIDATES er**
9. **BLOCK V4 — DEFINE THE ROOT CHOSEN BY QUERY**
10. **BLOCK V5 — CALCULATE D(E, er, Qi)**
11. **BLOCK V6 — OBSERVED CARDINALITY (LIGHT VERSION)**
12. **BLOCK V7 — SEMANTIC CLASSIFICATION OF RELATIONSHIPS**
13. **BLOCK V8 — TYPES OF RELATIONSHIPS TOUCHED BY EACH QUERY**
14. **BLOCK V9 — STRUCTURAL ANALYSIS OF EDGES BY DEPTH**
15. **BLOCK V10 — CALCULATE Re(Qi, er, D) AND DeltaR**
16. **BLOCK V11 — ASSEMBLE COMPACT MATRIX BY QUERY**
17. **BLOCK V12 — ANALYTICAL MATRIX OF IMDb (EXPANDED BY DEPTH)**
18. **BLOCK V13 — COMPACT ANALYTICAL MATRIX BY QUERY**
19. **BLOCK V14 — ENTITIES EXPLICITLY MODIFIED BY QUERY**
20. **BLOCK V15 — CALCULATE UPDATE VOLATILITY BY ENTITY**
21. **BLOCK V16 — SUMMARIZE UPDATE VOLATILITY BY QUERY**
22. **BLOCK V17 — INTEGRATE UPDATE VOLATILITY INTO THE ANALYTICAL MATRIX**
23. **BLOCK V18 — EXTRACT SHAREDNESS OBSERVED IN THE IMDb DATASET**
24. **BLOCK V19 — SUMMARIZE SHAREDNESS BY QUERY**
25. **BLOCK V20 — INTEGRATE SHAREDNESS INTO THE FINAL ANALYTICAL MATRIX**
26. **TRANSFORM ANALYTICAL MATRIX INTO CSV FOR RESULTS ANALYSIS** *(optional) export)*
27. **BLOCK V21A — FINAL MATRIX OF CALCULATED VARIABLES**
28. **BLOCK V21B — INFERRED ACTIVATION OF CLASSES AND GENERATION OF CANDIDATE CONFIGURATIONS FOR TESTING**
29. **BLOCK V22 — EXPANDED CATALOG OF MONGODB EXPERIMENTS**
30. **BLOCK V22B — SUMMARY TABLE WITH THE ORDER OF EXPERIMENTS**
31. **BLOCK V22C — COMPARISON MATRIX BY FAMILY**
32. **BLOCK V22D — BENCHMARK EXECUTION TEMPLATE**
33. **Save the DataFrames to a folder** *(optional utility block)*

### Main outputs after Part A
At the end of Part A you should have, at minimum:

- conceptual / analytical matrices;
- `document_variable_matrix_df`;
- inferred activation classes;
- `mongo_configuration_catalog_df`;
- `mongo_experiment_catalog_df`;
- benchmark execution template DataFrame;
- exported CSVs used by the benchmark runner.

---

## 7) How the load and benchmark were executed

After the notebook exported the required CSV files, the actual MongoDB load and benchmark were executed on the server using an external Python script.

Fill in the script name here:

- **Benchmark runner script:** `run_mongo_benchmark_option_b_incremental.py`

Typical command pattern:

```bash
python [ADD PYTHON SCRIPT NAME HERE]   --catalog-csv [PATH TO mongo_experiment_catalog.csv]   --template-csv [PATH TO benchmark_execution_template.csv]   --results-dir [OUTPUT DIRECTORY]   --mode all   --experiments [EXPERIMENT OR CONFIG LIST]   --query-group [primary|secondary_affected|control|all]   --run-phase [cold|hot|all]   --max-runs [N]   --force-rebuild   --verbose
```

### What this script does
The server-side script performs the following actions:

1. reads the experiment catalog;
2. reads the benchmark execution template;
3. connects to the MongoDB container;
4. creates the experimental database for each selected configuration;
5. loads the exported CSV data into the collections defined by the configuration;
6. creates the indexes required by the benchmarked queries;
7. executes the benchmark runs according to:
   - experiment,
   - query group,
   - run phase,
   - repetition count;
8. saves:
   - materialization summaries,
   - raw benchmark results,
   - aggregate benchmark results.

---

## 8) Notes about the load process

### Conceptual-model-driven load
The load into MongoDB is based on the conceptual-model-driven outputs of the framework. This means that the collections and embedded structures are built according to the activated configuration class and not by simply copying the source dataset tables directly into MongoDB.

### Batch-based insertion
The load was performed through batched inserts. The batch size can be adjusted in the benchmark runner.

Important practical note:

- **smaller batch sizes** make the load **more stable**, but also **slower**;
- **larger batch sizes** generally make the load **faster**, but they consume more memory and may increase pressure on the MongoDB container or on the server.

Document the default batch size used in your experiments here:

- **Default batch size used:** `1.000.000`



### Recommendation
If the load is too slow, first consider increasing the batch size. If the server has enough memory, larger batches usually improve throughput significantly.

---

## 9) Notes about benchmark execution settings

Document the main benchmark settings here:

- **Run phases executed:** `[ADD cold / hot / both]`
- **Number of repetitions per query:** `20`
- **Query groups executed:** `[ADD primary / secondary_affected / control / all]`


### Recommended interpretation
The benchmark should be interpreted by combining:

- **primary queries**: to measure the expected gain of the activated configuration;
- **secondary affected queries**: to measure the collateral effect on structurally related queries;
- **control queries**: to verify whether unrelated access paths remain stable.

---

## 11) What still needs to be documented manually

Before considering this README final, fill in the placeholders marked with brackets:

- repository URL;
- dataset repository / storage location;
- file explaining scale-factor generation;
- benchmark runner Python script name;
- MongoDB container connection data;
- batch size used in practice;
- run phases and repetition counts;
- output directory naming convention;
- any local server-specific paths.

---

## 12) Reproducibility checklist

Before starting a full execution, confirm that all items below are true:

- [ ] DuckDB environment is working
- [ ] All required TSV / extracted files exist
- [ ] Scale factor folders `sf0.25`, `sf0.5`, and `sf1` are available
- [ ] Notebook Part A was executed successfully
- [ ] CSV exports required by the benchmark runner were generated
- [ ] Docker is running
- [ ] MongoDB container is active and reachable
- [ ] Benchmark runner `.py` file is available on the server
- [ ] Batch size and benchmark options are configured
- [ ] Output directory exists or can be created

If all items are satisfied, the workflow is ready to run end-to-end.
