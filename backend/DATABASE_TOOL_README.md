# Database Tool Documentation

The `database_tool.py` utility provides a command-line interface for managing database operations, including:

- Creating and initializing the database
- Managing migrations
- Adding or updating user data
- Importing data from Excel files
- Database diagnostics and troubleshooting

## Usage

```bash
python database_tool.py [command] [options]
```

### Available Commands

- `init`: Initialize the database and create necessary tables
- `migrate`: Run database migrations
- `add-user`: Add a new user to the database
- `list-users`: List all users in the database
- `import`: Import users from Excel file
- `backup`: Create a database backup
- `restore`: Restore database from backup
- `check`: Check database health

### Options

Use `--help` with any command to see available options:

```bash
python database_tool.py [command] --help
```

## Examples

Initialize database:
```bash
python database_tool.py init
```

Create a new admin user:
```bash
python database_tool.py add-user --username admin --fullname "Administrator" --email admin@example.com --role admin
```

Import users from Excel:
```bash
python database_tool.py import --file users.xlsx
```