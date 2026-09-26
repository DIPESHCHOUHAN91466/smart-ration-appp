# Smart Ration C# business API (ASP.NET Core 8). Build from the REPOSITORY ROOT:
#   docker build -f backend/SmartRation.Api/Dockerfile -t smartration-csharp-api .
# The root .dockerignore is an allow-list: only this project's sources enter the build (no bin/obj,
# no secrets, no local SQLite files).
# Configuration comes from environment variables at run time, never from the image:
#   Database__Provider=MySql, ConnectionStrings__MySql, Jwt__Key (= the Python API's JWT_SECRET_KEY),
#   Qr__Secret, DATA_MODE, Demo__DemoOtpEnabled=false, Sms__Provider / Sms__AllowMockOutsideDevelopment.
# On first start against an EMPTY database it creates the schema (EF Core migrations, identical to the
# Alembic schema) and, in synthetic mode, seeds the demo data.

FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src
COPY backend/SmartRation.Api/SmartRation.Api.csproj backend/SmartRation.Api/
RUN dotnet restore backend/SmartRation.Api/SmartRation.Api.csproj
COPY backend/SmartRation.Api/ backend/SmartRation.Api/
RUN dotnet publish backend/SmartRation.Api/SmartRation.Api.csproj -c Release -o /app --no-restore

FROM mcr.microsoft.com/dotnet/aspnet:8.0
WORKDIR /app
COPY --from=build /app .
ENV ASPNETCORE_ENVIRONMENT=Production \
    DATA_MODE=synthetic \
    DOTNET_RUNNING_IN_CONTAINER=true
COPY backend/SmartRation.Api/docker-entrypoint.sh /app/docker-entrypoint.sh
# The aspnet image ships a non-root "app" user.
USER app
EXPOSE 8080
# Writes the database CA certificate (MYSQL_SSL_CA) if given, then listens on $PORT (8080 otherwise).
ENTRYPOINT ["sh", "/app/docker-entrypoint.sh"]
