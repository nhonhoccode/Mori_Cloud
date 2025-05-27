FROM python:3.10-slim
RUN apt-get update && apt-get install -y libpq-dev
WORKDIR /mori_super_search
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-deps torch==2.3.1+cpu torchvision==0.18.1+cpu -f https://download.pytorch.org/whl/torch_stable.html && \
    pip install -r requirements.txt
COPY . .
RUN ls -al /mori_super_search
ENV PYTHONUNBUFFERED 1
COPY mori.sh /mori_super_search/mori.sh
RUN chmod +x /mori_super_search/mori.sh
CMD ["/bin/bash", "/mori_super_search/mori.sh"]