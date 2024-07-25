# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the project code into the container
COPY . /app/

# Copy the wait-for-it script and make it executable
COPY wait-for-db.sh /app/wait-for-db.sh
RUN chmod +x /app/wait-for-db.sh

# Copy the entrypoint script and make it executable
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Create a non-root user and switch to it
RUN adduser --disabled-password --gecos '' appuser

# Create a directory for static files as root
RUN mkdir -p /main

# Change ownership of the directory to appuser
RUN chown -R appuser:appuser /main

# Change ownership of the /app directory to appuser
RUN chown -R appuser:appuser /app

USER appuser

# Expose the port the app runs on
EXPOSE 8000

# Set the entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]

# Command to run the application
CMD ["gunicorn", "-c", "gunicorn.conf.py", "resume_analyzer.wsgi:application"]