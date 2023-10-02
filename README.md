# LILAC: Log Parsing using LLMs with Adaptive Parsing Cache

This is the anonymous replication package for the FSE2024 submission #60 "LILAC: Log Parsing using LLMs with Adaptive Parsing Cache".
The detailed parsing time can be found in [full parsing time](figures/parsing_time.png).

## Repository Organization 

```
├── full_dataset/ # Please download and unzip full datasets into this directory
│   └── sampled_examples # Our saved sampled candidates
├── benchmark/
│   ├── evaluation/ # the evaluation code of LILAC
│   └── logparser/ # the implementation code of LILAC
├── result/
│   └── ...... # contains the saved evaluation files
├── sampling/ # the implementation of candidate sampling algorithms
│   ├── logppt_sampling.py # the sampling algorithm of LogPPT
│   └── LILAC_sampling.py # the sampling algorithm of LILAC
├── requirements.txt
├── openai_key.txt # the OpenAI api address and key
└── README.md
```


## Datasets

Please first download the large-scale datasets for log parsing in LogPub from [Zenodo](https://zenodo.org/record/8275861) and unzip these datasets into the directory of `full_dataset`.


## Installation

1. Install ```python >= 3.8```
2. ```pip install -r requirements.txt```


## Execution

### Candidate Sampling

We have provided the saved sampled candidate logs for reproducing.

One can also delete the `full_dataset/sampled_examples` and execute the LILAC's sampling algorithm as follows:

```bash
cd sampling/
python LILAC_sampling
```

### Online Log Parsing

Please first add an OpenAI API key (`sk-xxxx`) into the second line of openai_key.txt.

We provide a one-click script to run LILAC for online log parsing.

```bash
./online_parsing.sh
```

One can also go to `benchmark/evaluation` and execute:

```bash
python LILAC_eval.py --shot [candidates] --example_size [demonstrations] --model [model]
```

The parsed results and evaluation results will be saved in the `result/` directory.

We have provided the saved evaluation metric files of LILAC with different settings in the directory of `result/`.
Besides, we provide the fully parsed results of LILAC in default settings (i.e. 32 candidates, 3 demonstrations and ChatGPT) in [anonymous Google Drive](https://drive.google.com/file/d/1OJcPjHCEjBIz1rCR98CO27JDX1O9AP7f/view?usp=share_link).

### Running Sample:

```bash
=== Evaluation on Proxifier ===
start parsing.
Parsing file: ../../full_dataset/Proxifier/Proxifier_full.log
===========================================
Line-0/21320: No match. proxy.cse.cuhk.edu.hk:5070 close, 0 bytes sent, 0 bytes received, lifetime <1 sec
model:  gpt-3.5-turbo-0613
queried_new_template:  <*> close, <*> bytes sent, <*> bytes received, lifetime <*>
===========================================
Query times:  1
===========================================
```