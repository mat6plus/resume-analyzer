# Resume Analyzer

This is a free and a simple open-source tool to analyze your resume against a Job position.
If you find this useful don't forget to drop a like. Thanks

1. Save this Makefile in the root directory of your project, where your docker-compose.yml file is located.

2. To use the Makefile, you'll run commands using `make` followed by the target name. Here are the available commands:

   - `make build`: Builds your Docker images.
   - `make up`: Starts your application in detached mode.
   - `make down`: Stops your application.
   - `make restart`: Restarts your application (stops and then starts).
   - `make logs`: Shows the logs of your running containers.
   - `make shell`: Opens a bash shell in your main application container.
   - `make clean`: Removes stopped containers and unused images.
   - `make deploy`: Builds the images and starts the application.

3. To build and start your application in one command, you can run:
   ```
   make deploy
   ```

4. If you want to build the images without starting the containers, run:
   ```
   make build
   ```

5. To start the application after building, run:
   ```
   make up
   ```

6. To stop the application, use:
   ```
   make down
   ```

7. If you need to view the logs, use:
   ```
   make logs
   ```

This Makefile assumes that your main application service in the docker-compose.yml file is named 'resume-analyzer'. If it's named differently, you should update the `APP_NAME` variable at the top of the Makefile.

Also, make sure you have `make` installed on your system. It's usually pre-installed on most Unix-based systems (Linux, macOS), but you might need to install it separately on Windows.

This Makefile provides a convenient way to manage your Docker Compose workflow. You can easily extend it with more commands as needed for your specific project requirements.

---

In a production environment, it's generally best to have your application start automatically. This ensures that your service comes back online if the server restarts unexpectedly or after planned maintenance. There are several ways to achieve this automation, depending on your hosting environment and preferences. I'll outline a few common approaches:

1. System Init (systemd)
2. Docker Swarm or Kubernetes
3. Cloud-specific solutions

Let's focus on using systemd, as it's a common and versatile option that works well with Docker Compose.



```ini
[Unit]
Description=Resume Analyzer Docker Compose Application
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/path/to/your/project
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target

```

Here's how to set up and use this systemd service:

1. Save this file as `resume-analyzer.service` in the `/etc/systemd/system/` directory on your production server.

2. Replace `/path/to/your/project` with the actual path to your project directory containing the docker-compose.yml file.

3. Make sure the paths to `docker-compose` are correct. You can find the correct path by running `which docker-compose` on your server.

4. Reload the systemd manager to recognize the new service:
   ```
   sudo systemctl daemon-reload
   ```

5. Enable the service to start on boot:
   ```
   sudo systemctl enable resume-analyzer.service
   ```

6. Start the service:
   ```
   sudo systemctl start resume-analyzer.service
   ```

Now, your application will start automatically when the server boots up. You can also manually control it using systemctl:

- To start: `sudo systemctl start resume-analyzer.service`
- To stop: `sudo systemctl stop resume-analyzer.service`
- To restart: `sudo systemctl restart resume-analyzer.service`
- To check status: `sudo systemctl status resume-analyzer.service`

This approach has several advantages:
- It automatically starts your application on server boot.
- It provides a standard way to start, stop, and check the status of your application.
- It integrates with the host system's logging (journalctl).

Additional considerations for production:

1. Logging: Ensure your Docker containers are configured to log appropriately. You might want to use a centralized logging solution.

2. Monitoring: Set up monitoring for both the host system and your containers. Tools like Prometheus, Grafana, or cloud-specific monitoring solutions can help.

3. Backups: Implement regular backups of your data, especially if you're using volumes for persistent storage.

4. Updates: Have a strategy for updating your application. This might involve setting up a CI/CD pipeline.

5. Security: Ensure your Docker daemon and containers are properly secured. This includes using non-root users in containers, keeping software updated, and following security best practices.

6. High Availability: For critical applications, consider setting up multiple instances behind a load balancer.

Remember, the exact setup might vary depending on your specific hosting environment. If you're using a cloud provider, they often have their own solutions for container orchestration and automating deployments, which might be worth exploring.