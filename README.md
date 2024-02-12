# Supercharge Slackbots with RAG in real-time

Join [Bytewax](https://bytewax.io), [Soflandia](https://softlandia.fi) and [AIcamp](https://aicamp.ai) for a free virtual workshop on Feb 16th, 2024.
RSVP [here](https://www.aicamp.ai/event/eventdetails/W2024021609).

- Skill level
    
    **Intermediate, comfortable with Python**
    
- Time to complete
    
    **Approx. 2 hours**
    

## ****Prerequisites****

TBD

**Python modules**

bytewax, qdrant-client

## Your Takeaway

*Your takeaway from this workshop will be a RAG supercharged slackbot.*

## Table of content

- Resources
- Introduction
- Setup
- A basic data stream
- LLM + RAG
- Bonus! Feedback loop
- Recap

## Resources

TBD

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
pip install bytewax==0.18.1
```

Read more about installing Bytewax in [our documentation](https://bytewax.io/docs/getting-started/installation).

### Install and configure the Qdrant vector database
Get the Python client with

```bash
pip install 'qdrant-client[fastembed]'
```

The client uses an in-memory database. You can even run it in Colab or Jupyter Notebook, no extra dependencies required. See an [example](https://colab.research.google.com/drive/1Bz8RSVHwnNDaNtDwotfPj0w7AYzsdXZ-?usp=sharing).

## 3. A basic data stream (20 minutes)
This step is to build a basic data stream. The central concept of Bytewax is a dataflow, which provides the necessary building blocks for choreographing the flow of data. Within Bytewax, a dataflow is a Python object that outlines how data will flow from input sources, the transformations it will undergo, and how it will eventually be passed to the output sinks.

Here, we will be using Slack as an input source, and [`StdOutSink`](https://bytewax.io/apidocs/bytewax.connectors/stdio#bytewax.connectors.stdio.StdOutSink) as a sink.

> Bytewax connects to a variety of input sources and output sinks, check out our [Getting Started example](https://bytewax.io/docs/getting-started/simple-example), [Polling Input Example](https://bytewax.io/docs/getting-started/polling-input-example), and more in [the blog](https://bytewax.io/blog).

## 4. LLM + RAG (40 minutes)
The central part of the workshop covers LLM and RAG. We'll track what the conversation is about using LLM. We'll branch our stream to separate messages that contain a query. To generate responses to the queries, we will use LLM and RAG techniques.

## 5. Bonus! Feedback loop (20 minutes, if time allows)
Once we build our pipeline, we can ask questions and receive RAG-enriched responses. But so far, we've been using the `StdOutSink`. In this step, we replace it and will see how to push responses back to a Slack channel.

## 5. Recap (15 minutes)
We'll wrap up with a demo! And discuss what we learned and where to go next.

Hope to see you there!
[RSVP](https://www.aicamp.ai/event/eventdetails/W2024021609)

## We want to hear from you!

If you have any trouble with the process or have ideas about how to improve this document, come talk to us in the #questions-answered [Slack channel](https://join.slack.com/t/bytewaxcommunity/shared_invite/zt-1lhq9bxbr-T3CXxR_9RIUGb4qcBK26Qw)!

## Where to next?

[Share your progress!](https://twitter.com/intent/tweet?text=I%27m%20mastering%20RAG%20apps%20with%20%40bytewax!%20&url=https://bytewax.io/tutorials/&hashtags=Bytewax,Tutorials)
