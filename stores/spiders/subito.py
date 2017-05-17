import scrapy
import re
import sys
import logging

log = logging.getLogger()

class Subito(scrapy.Spider):
	name = 'subito'

	def __init__(self, query='', *args, **kwargs):
		super(Subito, self).__init__(*args, **kwargs)
		query = query.replace(" ", "+")		
		self.start_urls = ['http://www.subito.it/annunci-italia/vendita/usato/?q=%s' % query]
		self.obj = {}

	def parse(self, response):
		for item in response.css('.items_listing li'):
			self.obj['title'] = item.css('.item_description h2 a::text').extract_first()
			try:
				non_decimal = re.compile(r'[^\d.]+')
				self.obj['price'] = non_decimal.sub(' ', item.css('.item_price::text').extract_first())
			except TypeError as e:
				self.obj['price'] = 0.00
			self.obj['date'] = item.css('time::attr(datetime)').extract_first()
			self.obj['place'] = item.css('.item_location::text').extract_first()
			self.obj['link'] = item.css('.item_description h2 a::attr(href)').extract_first()
			self.obj['img'] = item.css('.item_image_wrapper img::attr(src)').extract_first()
			# recupero descrizione
			detail_page = response.urljoin(self.obj['link'])
			if self.obj['title'] is not None:
				yield self.obj
				# yield scrapy.Request(detail_page, callback=self.parseDetails)

		next_page = response.css('div.pagination_next a::attr(href)').extract_first()
		if next_page is not None:
			next_page = "http://www.subito.it%s" % next_page
			next_page = response.urljoin(next_page)
			yield scrapy.Request(next_page, callback=self.parse)

	def parseDetails(self, response):
		description = response.css('#ad_details .description::text').extract_first()
		img = response.css('.main_image_wrapper .image img::attr(src)').extract_first()
		self.obj['description'] = description
		self.obj['img'] = img
		yield self.obj
