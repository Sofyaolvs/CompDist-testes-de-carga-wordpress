# Serviço de extração de links (versão Ruby): GET /api/<url> -> JSON com os links da página.
require "sinatra"
require "json"
require "net/http"
require "nokogiri"
require "redis"
require "uri"

set :environment, :production
set :logging, false

USAR_CACHE = ENV.fetch("CACHE", "on") == "on"
CACHE = Redis.new(host: ENV.fetch("REDIS_HOST", "redis"), port: 6379)

def normalizar(url)
  url =~ %r{\Ahttps?://} ? url : "http://#{url}"
end

def extrair_links(url)
  html = Net::HTTP.get(URI(url))
  Nokogiri::HTML(html).css("a[href]").map { |a| URI.join(url, a["href"]).to_s }
end

get "/health" do
  "ok"
end

get "/api/*" do
  url = normalizar(params["splat"].first)
  corpo = USAR_CACHE ? CACHE.get(url) : nil
  if corpo.nil?
    corpo = JSON.generate(extrair_links(url))
    CACHE.set(url, corpo) if USAR_CACHE
  end
  content_type :json
  corpo
end
