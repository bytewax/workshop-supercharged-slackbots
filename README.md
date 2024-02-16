# Supercharge Slackbots with RAG in real-time

Join [Bytewax](https://bytewax.io), [Soflandia](https://softlandia.fi) and [AIcamp](https://aicamp.ai) for a free virtual workshop on Feb 16th, 2024.
RSVP [here](https://www.aicamp.ai/event/eventdetails/W2024021609).

- Skill level
    
    **Intermediate, comfortable with Python**
    
- Time to complete
    
    **Approx. 2 hours**
    

## Your Takeaway

*Your takeaway from this workshop will be a RAG supercharged slackbot.*

![demo](https://github.com/bytewax/workshop-supercharged-slackbots/assets/8543707/e63ae750-da72-40b8-875e-fb0bd254a7df)


## Table of content

- Resources
- Introduction
- Setup
- A basic data stream
- LLM + RAG
- Bonus! Feedback loop
- Recap

## Resources

- Join our Workshop Slack (this is the workspace where the bot is installed): https://join.slack.com/t/bytewaxworkshop/shared_invite/zt-2cesxqsgn-RDj6SUQYhTELZKDTOnoScA
- LLM API is provided to you by Softlandia, instructions will be shared in Workshop Slack when the workshop starts. You can also use your own API key with the standard OpenAI API, for example to use the latest and greatest language models. Instructions for that can be found in the .env -file.
- A sample dataset is located in data/dataset.txt. Feel free to add additional documents.

## 1. Introduction (5 minutes)

We'll start with a brief introduction of the technologies we will use.

* [Bytewax](https://github.com/bytewax/bytewax) is a Python-native open-source framework and distributed stream processing engine. Made to build streaming data pipelines and real-time apps with everything needed. Able to run in the cloud, on-prem and on edge devices.
* [Qdrant](https://github.com/qdrant/qdrant) is a vector database & vector similarity search engine. It deploys as an API service providing search for the nearest high-dimensional vectors. Qdrant's expanding features allow for all sorts of neural network or semantic-based matching, faceted search, and other applications.
* LLM (Large Language Model) is an advanced AI model for generating human-like text. Trained on extensive datasets, it excels in various NLP tasks, offering contextually relevant responses. Ideal for automated customer service, content creation, and more, LLMs enhance communication across platforms. In this workshop, we'll be using [YOKOT.AI](https://yokot.ai/), Softlandia's flagship Generative AI Solution. It lets the user chat with their documents, crawl the internet for more documents, and generate new content based on existing documents and user input. Watch YOKOT.AI demo on [YouTube](https://www.youtube.com/watch?v=iovG0-9RL1E).
* RAG (Retrieval Augmented Generation) is an AI architecture that boosts Large Language Model (LLM) capabilities by integrating retrieval-based information with generative responses. This approach allows for more accurate and detailed answers to complex queries, enhancing the overall LLM experience by providing contextually enriched content. For further reading on RAG and YOKOT.AI please refer to [this article](https://softlandia.fi/en/blog/microsoft-365-copilot-grok-chatgpt-and-yokot-ai-a-look-into-rags).

We will also go through the agenda and pre-shared materials.

## 2. Setup (20 minutes)

### Install and configure Bytewax into a Python environment
Bytewax currently supports the following versions of Python: 3.8, 3.9, 3.10 and 3.11. 

> We recommend creating a virtual environment for your project when installing Bytewax. For more information on setting up a virtual environment, see the [Python documentation](https://docs.python.org/3.11/tutorial/venv.html).

Once you have your environment set up, you can install Bytewax. We recommend that you pin the version of Bytewax that you are using in your project by specifying the version of Bytewax that you wish to install:

```bash
pip install -r requirements.txt
```

Read more about installing Bytewax in [our documentation](https://bytewax.io/docs/getting-started/installation).


### Install and configure Qdrant vector database

The client uses an in-memory database. You can even run it in Colab or Jupyter Notebook, no extra dependencies required. See an [example](https://colab.research.google.com/drive/1Bz8RSVHwnNDaNtDwotfPj0w7AYzsdXZ-?usp=sharing).

### Run the stream!

Run the stream with:

```bash
python -m bytewax.run <module>
```

For example if your stream is defined in `my_stream.py` in the repository root, you would run:

```bash
python -m bytewax.run my_stream
```

## 3. A basic data stream (20 minutes)
This step is to build a basic data stream. The central concept of Bytewax is a dataflow, which provides the necessary building blocks for choreographing the flow of data. Within Bytewax, a dataflow is a Python object that outlines how data will flow from input sources, the transformations it will undergo, and how it will eventually be passed to the output sinks.

Here, we will be using Slack as an input source, and [`StdOutSink`](https://bytewax.io/apidocs/bytewax.connectors/stdio#bytewax.connectors.stdio.StdOutSink) as a sink.

> Bytewax connects to a variety of input sources and output sinks, check out our [Getting Started example](https://bytewax.io/docs/getting-started/simple-example), [Polling Input Example](https://bytewax.io/docs/getting-started/polling-input-example), and more in [the blog](https://bytewax.io/blog).

## 4. LLM + RAG (40 minutes)
The central part of the workshop covers LLM and RAG. We'll track what the conversation is about using LLM. We'll branch our stream to separate messages that contain a query. To generate responses to the queries, we will use LLM and RAG techniques. Let's take a look at the diagram: 

![diagram](https://github.com/bytewax/workshop-supercharged-slackbots/assets/8543707/e2e3afa7-b15a-4bff-b79c-cffb528d3e01)

* **[Slack API](https://api.slack.com/)**: This is where the workflow initiates, with the system receiving textual input through Slack's API.

* **Process Text:** In this phase, we analyze the input text to determine whether it is a statement or a question/query. If it is identified as a statement, it is sent to Yokot.AI for a summary. If the text is a question, it will be passed down a different workflow path to find an answer

* **Prompt LLM:** During this step, the system engages with an LLM (Yokot.AI) to generate summaries and formulate responses depending on the type of input identified in the previous step.

* **Summarize:** Summaries generated by the LLM are stored in Bytewax's state and can be accessed as needed. Note that if scaling is required, Bytewax manages this state across various workers, ensuring data is routed correctly for stateful operations.

* **Find an Answer:** To find canonical answers to questions, the system leverages data from preloaded documents and the Qdrant component. These answers also take into account the summaries that have been generated and stored in the state. Embeddings will be created using Qdrant with [fastembed](https://qdrant.github.io/fastembed/Getting%20Started/).

* **Response:** The final step is to send the responses back. For simplicity, we will start with the [`StdOutSink`](https://bytewax.io/apidocs/bytewax.connectors/stdio#bytewax.connectors.stdio.StdOutSink) and switch to the Slack API if time allows.

## 5. Bonus! Feedback loop (20 minutes, if time allows)
Once we build our pipeline, we can ask questions and receive RAG-enriched responses. But so far, we've been using the `StdOutSink`. In this step, we replace it and will see how to push responses back to a Slack channel.

## 6. Recap (15 minutes)
We'll wrap up with a demo! And discuss what we learned and where to go next.

Hope to see you there!
[RSVP](https://www.aicamp.ai/event/eventdetails/W2024021609)

## We want to hear from you!

If you have any trouble with the process or have ideas about how to improve this document, come talk to us in the #questions-answered [Slack channel](https://join.slack.com/t/bytewaxcommunity/shared_invite/zt-1lhq9bxbr-T3CXxR_9RIUGb4qcBK26Qw)!

## Where to next?

[Share your progress!](https://twitter.com/intent/tweet?text=I%27m%20mastering%20RAG%20apps%20with%20%40bytewax!%20&url=https://bytewax.io/tutorials/&hashtags=Bytewax,Tutorials)
