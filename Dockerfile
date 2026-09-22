FROM node:22-alpine AS frontend
WORKDIR /frontend
COPY package.json ./
COPY package-lock.json* ./
RUN npm install
COPY index.html main.jsx style.css ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY *.py ./
COPY --from=frontend /frontend/dist ./dist
ENV PORT=8000
EXPOSE 8000
CMD ["sh","-c","uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
