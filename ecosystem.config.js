module.exports = {
  apps: [
    {
      name: 'n8n',
      script: 'powershell.exe',
      args: '-NoProfile -ExecutionPolicy Bypass -File n8n.ps1',
      cwd: __dirname,
      autorestart: true,
      max_restarts: 10,
      restart_delay: 5000,
    },
  ],
};
