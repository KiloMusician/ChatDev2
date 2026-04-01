import requests
from bs4 import BeautifulSoup
import openai
import wikipediaapi
import os

self_api_key = os.environ.get('OPENAI_API_KEY')
BASE_URL = os.environ.get('BASE_URL')

# Initialize OpenAI client with proper error handling
try:
    # Try basic client initialization with proper parameters
    client_kwargs = {}
    if self_api_key:
        client_kwargs['api_key'] = self_api_key
    if BASE_URL:
        client_kwargs['base_url'] = BASE_URL
    
    client = openai.OpenAI(**client_kwargs)
    print("OpenAI client initialized successfully")
except Exception as e:
    print(f"Error initializing OpenAI client: {e}")
    print("Creating a stub client to prevent crashes...")
    # Create a minimal stub that matches the real API structure
    class StubClient:
        class chat:
            class completions:
                @staticmethod
                def create(**kwargs):
                    return type('Response', (), {
                        'choices': [type('Choice', (), {
                            'message': type('Message', (), {'content': 'API not available'})()
                        })()]
                    })()
    client = StubClient()

def get_baidu_baike_content(keyword):
    # design api by the baidubaike
    url = f'https://baike.baidu.com/item/{keyword}'
    # post request
    response = requests.get(url)

    # Beautiful Soup part for the html content
    soup = BeautifulSoup(response.content, 'html.parser')
    # find the main content in the page
    # main_content = soup.find('div', class_='lemma-summary')
    main_content = soup.contents[-1].contents[0].contents[4].attrs['content']
    # find the target content
    # content_text = main_content.get_text().strip()
    return main_content


def get_wiki_content(keyword):
    #  Wikipedia API ready
    wiki_wiki = wikipediaapi.Wikipedia('MyProjectName (merlin@example.com)', 'en')
    #the topic content which you want to spider
    search_topic = keyword
    # get the page content
    page_py = wiki_wiki.page(search_topic)
    # check the existence of the content in the page
    if page_py.exists():
        print("Page - Title:", page_py.title)
        print("Page - Summary:", page_py.summary)
    else:
        print("Page not found.")
    return page_py.summary



def modal_trans(task_dsp):
    try:
        task_in ="'" + task_dsp + \
               "'Just give me the most important keyword about this sentence without explaining it and your answer should be only one keyword."
        messages = [{"role": "user", "content": task_in}]
        response = client.chat.completions.create(
            messages=messages,
            model="gpt-3.5-turbo-16k",
            temperature=0.2,
            top_p=1.0,
            n=1,
            stream=False,
            frequency_penalty=0.0,
            presence_penalty=0.0,
            logit_bias={}
        )
        
        # Handle response properly for both real API and stub client
        try:
            if hasattr(response, 'choices') and response.choices:
                response_text = response.choices[0].message.content
            else:
                response_text = 'default_keyword'
        except (AttributeError, IndexError):
            response_text = 'default_keyword'
            
        spider_content = get_wiki_content(response_text)
        # time.sleep(1)
        task_in = "'" + spider_content + \
               "',Summarize this paragraph and return the key information."
        messages = [{"role": "user", "content": task_in}]
        response = client.chat.completions.create(
            messages=messages,
            model="gpt-3.5-turbo-16k",
            temperature=0.2,
            top_p=1.0,
            n=1,
            stream=False,
            frequency_penalty=0.0,
            presence_penalty=0.0,
            logit_bias={}
        )
        
        # Handle response properly for both real API and stub client
        try:
            if hasattr(response, 'choices') and response.choices:
                result = response.choices[0].message.content
            else:
                result = spider_content[:200] if spider_content else 'No content available'
        except (AttributeError, IndexError):
            result = spider_content[:200] if spider_content else 'No content available'
            
        print("web spider content:", result)
    except Exception as e:
        print(f"Error in modal_trans: {e}")
        result = ''
        print("the content is none")
    return result