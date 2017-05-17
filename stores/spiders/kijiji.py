import scrapy
import re
import sys
import logging
import datetime

log = logging.getLogger()

class Kijiji(scrapy.Spider):
	name = 'kijiji'

	def __init__(self, query='', *args, **kwargs):
		super(Kijiji, self).__init__(*args, **kwargs)
		query = query.replace(" ", "+")
		self.start_urls = ['https://www.kijiji.it/%s/' % query]

	def parse(self, response):
		for item in response.css('#search-result li'):
			obj = {}
			title = item.css('.item-content h3.title a::text').extract_first()
			if title is not None:
				obj['title'] = title.strip()
				try:
					non_decimal = re.compile(r'[^\d.]+')
					obj['price'] = non_decimal.sub("", item.css('.item-content h4.price::text').extract_first())
				except:
					obj['price'] = 0
				obj['place'] = item.css('.item-content p.locale::text').extract_first()
				obj['link'] = item.css('.item-content h3.title a::attr(href)').extract_first()
				obj['img'] = "http:%s" % item.css('p.thumbnail img::attr(src)').extract_first()
				time = item.css('.item-content p.timestamp::text').extract_first()
				m = re.search('\d{2}:\d{2}', time)
				if m:
					obj['time'] = m.group(0)
				else:
					obj['time'] = '00:00'
				# recupero data
				detail_page = response.urljoin(obj['link'])
				yield scrapy.Request(detail_page, callback=self.parseDetails, meta={'obj':obj})

		next_page = response.css('nav#pagination a.btn-pagination-forward::attr(href)').extract_first()
		if next_page is not None:
			next_page = "https://www.kijiji.it%s" % next_page
			next_page = response.urljoin(next_page)
			yield scrapy.Request(next_page, callback=self.parse)


	def parseDetails(self, response):
		obj = response.meta['obj']
		try:
			data = response.css('article.vip__informations .vip__informations__block')[1].css('span.vip__informations__value::text').extract_first().strip()
			obj['data'] = "%s %s:00" % (datetime.datetime.strptime(data, "%d/%m/%y").strftime('%Y-%m-%d'), obj['time'])
		except:
			obj['data'] = "ND"
		yield obj