FROM ruby:3.3
WORKDIR /app
COPY Gemfile .
RUN bundle install
COPY main.rb config.ru ./
EXPOSE 5000
# 4 processos x 4 threads, como o Gunicorn da versão Python
CMD ["bundle", "exec", "puma", "-w", "4", "-t", "4:4", "-b", "tcp://0.0.0.0:5000", "config.ru"]
