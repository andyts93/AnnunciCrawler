import scrapy
import re
import sys
import MySQLdb
import logging

log = logging.getLogger()

class Subito(scrapy.Spider):
	name = 'subito'

	def __init__(self, query='', *args, **kwargs):
		super(Subito, self).__init__(*args, **kwargs)
		self.conn = MySQLdb.connect(host="localhost",user="scraper",passwd="scraper",db="scraper",use_unicode=True,charset="utf8")
		self.x = self.conn.cursor()
		query = query.replace(" ", "+")		
		self.start_urls = ['http://www.subito.it/annunci-italia/vendita/usato/?q=%s' % query]

	def parse(self, response):
		for item in response.css('.items_listing li'):
			obj = {}
			obj['title'] = item.css('.item_description h2 a::text').extract_first()
			try:
				non_decimal = re.compile(r'[^\d.]+')
				obj['price'] = non_decimal.sub(' ', item.css('.item_price::text').extract_first())
			except TypeError as e:
				obj['price'] = 0.00
			obj['date'] = item.css('time::attr(datetime)').extract_first()
			obj['place'] = item.css('.item_location::text').extract_first()
			obj['link'] = item.css('.item_description h2 a::attr(href)').extract_first()
			# recupero descrizione
			detail_page = response.urljoin(obj['link'])
			if obj['title'] is not None:
				try:
					self.x.execute("""INSERT INTO annunci (sito, title, price, date, place, link) VALUES (1, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE price = %s, date = %s, place = %s""",(obj['title'], obj['price'], obj['date'], obj['place'], obj['link'], obj['price'], obj['date'], obj['place']))
					self.conn.commit()
					yield scrapy.Request(detail_page, callback=self.parseDetails)
				except:
					log.error("Errore nell'inserimento dell'annuncio")
					self.conn.rollback()				

		next_page = response.css('div.pagination_next a::attr(href)').extract_first()
		if next_page is not None:
			next_page = "http://www.subito.it%s" % next_page
			next_page = response.urljoin(next_page)
			yield scrapy.Request(next_page, callback=self.parse)

	def parseDetails(self, response):
		description = response.css('#ad_details .description::text').extract_first()
		try:
			self.x.execute("""UPDATE annunci SET descrizione = %s WHERE link = %s""", (description, response.url))
			self.conn.commit()
		except MySQLdb.Error, e:
			log.error("Error [%d]: %s" % (e.args[0], e.args[1]))
			self.conn.rollback()

		img = response.css('.main_image_wrapper .image img::attr(src)').extract_first()
		if img is not None:
			try:
				self.x.execute("""UPDATE annunci SET immagine = %s WHERE link = %s""", (img, response.url))
				self.conn.commit()
			except MySQLdb.Error, e:
				log.error("Error [%d]: %s" % (e.args[0], e.args[1]))
				self.conn.rollback()		
