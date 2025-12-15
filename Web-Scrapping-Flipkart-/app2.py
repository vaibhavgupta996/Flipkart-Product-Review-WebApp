from flask import Flask, render_template, request
from flask_cors import CORS, cross_origin
import requests
from bs4 import BeautifulSoup as bs
import logging
import pymongo
import csv

# Logging setup
logging.basicConfig(filename="scrapper.log", level=logging.INFO)

# Flask setup
app = Flask(__name__)
CORS(app)

@app.route('/', methods=['GET'])
@cross_origin()
def homepage():
    return render_template('index.html')


@app.route('/review', methods=['POST', 'GET'])
@cross_origin()
def index():
    if request.method == 'POST':
        try:
            searchstring = request.form['content'].replace(" ", "")
            flipkart_url = "https://www.flipkart.com/search?q=" + searchstring

            # Add headers to avoid 403 Forbidden
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/115.0 Safari/537.36"
            }

            resp = requests.get(flipkart_url, headers=headers)
            resp.raise_for_status()  # Throw error if status != 200
            flipkart_html = bs(resp.text, "html.parser")

            bigboxes = flipkart_html.findAll("div", {"class": "cPHDOP col-12-12"})
            del bigboxes[0:3]  # removing irrelevant divs
            box = bigboxes[0]
            productlink = "https://www.flipkart.com" + box.div.div.div.a['href']

            prodRes = requests.get(productlink, headers=headers)
            prodRes.encoding = 'utf-8'
            prod_html = bs(prodRes.text, "html.parser")
            commentboxes = prod_html.findAll('div', {'class': "RcXBOT d7A196"})

            reviews = []

            # Save to CSV
            filename = searchstring + ".csv"
            logging.info("File Created Successfully")
            with open(filename, "w", newline='', encoding='utf-8') as fw:
                writer = csv.writer(fw)
                writer.writerow(["Product", "Customer Name", "Rating", "Heading", "Comment"])

                for commentbox in commentboxes:
                    try:
                        Name = commentbox.div.div.find_all('p', {"class": "_2NsDsF AwS1CA"})[0].text
                    except:
                        Name = "No Name"
                        logging.info("No Name")

                    try:
                        rating = commentbox.div.div.div.div.text
                    except:
                        rating = "No Rating"
                        logging.info("No Rating")

                    try:
                        commenthead = commentbox.div.div.div.p.text
                    except:
                        commenthead = "No Comment Heading"
                        logging.info("No Comment Heading")

                    try:
                        com_tag = commentbox.find_all('div', {'class': "ZmyHeo"})[0].div.text
                    except:
                        com_tag = "No Comment"
                        logging.info("No Comment")

                    mydict = {
                        "Product": searchstring,
                        "Customer Name": Name,
                        "Rating": rating,
                        "Heading": commenthead,
                        "Comment": com_tag
                    }
                    reviews.append(mydict)
                    writer.writerow([searchstring, Name, rating, commenthead, com_tag])
                    logging.info("Product: {}, Customer Name: {}, Rating: {}, Heading: {}, Comment: {}".format(
                        searchstring, Name, rating, commenthead, com_tag))

            logging.info("log my final result {} ".format(reviews))

            # Save to MongoDB
            client = pymongo.MongoClient("mongodb+srv://cu23250393:vaibhav3008@cluster0.deu7fv4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
            db = client['reviews_of_product']
            reviews_coll = db['reviews_of_product']
            reviews_coll.insert_many(reviews)

            return render_template('result.html', reviews=reviews[0:(len(reviews) - 1)])
        except Exception as e:
            logging.info("Error occurred: {}".format(e))
            return f"Something went wrong: {e}"
    else:
        return render_template('index.html')


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
