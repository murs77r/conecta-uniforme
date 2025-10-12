# Imagem base com PHP e Apache
FROM php:8.1-apache

# Informações do mantenedor
LABEL maintainer="Conecta Uniforme"
LABEL description="Sistema de compra de uniformes escolares"

# Instalar extensões PHP necessárias
RUN docker-php-ext-install mysqli pdo pdo_mysql

# Habilitar mod_rewrite do Apache (para URLs amigáveis)
RUN a2enmod rewrite

# Instalar utilitários úteis
RUN apt-get update && apt-get install -y \
    git \
    curl \
    zip \
    unzip \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Configurar DocumentRoot do Apache
ENV APACHE_DOCUMENT_ROOT=/var/www/html/conecta-uniforme
RUN sed -ri -e 's!/var/www/html!${APACHE_DOCUMENT_ROOT}!g' /etc/apache2/sites-available/*.conf
RUN sed -ri -e 's!/var/www/!${APACHE_DOCUMENT_ROOT}!g' /etc/apache2/apache2.conf /etc/apache2/conf-available/*.conf

# Configurar permissões do Apache
RUN echo '<Directory /var/www/html/conecta-uniforme>' >> /etc/apache2/apache2.conf && \
    echo '    Options Indexes FollowSymLinks' >> /etc/apache2/apache2.conf && \
    echo '    AllowOverride All' >> /etc/apache2/apache2.conf && \
    echo '    Require all granted' >> /etc/apache2/apache2.conf && \
    echo '</Directory>' >> /etc/apache2/apache2.conf

# Configurar timezone
RUN ln -snf /usr/share/zoneinfo/America/Sao_Paulo /etc/localtime && \
    echo "America/Sao_Paulo" > /etc/timezone && \
    echo "date.timezone=America/Sao_Paulo" > /usr/local/etc/php/conf.d/timezone.ini

# Copiar arquivos da aplicação
COPY . /var/www/html/conecta-uniforme/

# Definir diretório de trabalho
WORKDIR /var/www/html/conecta-uniforme

# Ajustar permissões
RUN chown -R www-data:www-data /var/www/html/conecta-uniforme && \
    chmod -R 755 /var/www/html/conecta-uniforme

# Expor porta 80
EXPOSE 80

# Comando para iniciar o Apache
CMD ["apache2-foreground"]
