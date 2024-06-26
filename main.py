#!/usr/bin/env python3
import os
import sys
import getpass
from collections import OrderedDict

MYSQL_TEXT = "MySQL"
POSTGRESQL_TEXT = "PostgreSQL"


def create_env_file(dir_name, env_variables):
    env_file_path = os.path.join(dir_name, "env", ".env")

    try:
        os.makedirs(os.path.dirname(env_file_path), exist_ok=True)

        if not os.path.exists(env_file_path):
            with open(env_file_path, "w") as env_file:
                for key, value in env_variables.items():
                    env_file.write(f"{key}={value}\n")
            print(f"Created {env_file_path}")
            print("")
        else:
            print(f"Env file already exists at {env_file_path}")

    except OSError as e:
        print(f"Error: {e}")


def generate_deploy_script(path_names):
    with open("deploy_services.sh", "w") as script_file:
        script_file.write("""#!/bin/bash\n\n""")
        script_file.write("""# Exit immediately if any command fails\nset -e\n\n""")
        script_file.write("""# Function to deploy a service\n""")
        script_file.write("""deploy_service() {\n""")
        script_file.write(""" local service_dir=$1\n""")
        script_file.write(""" echo "Deploying $service_dir"\n""")
        script_file.write(""" cp docker-compose.yml $service_dir/\n""")
        script_file.write(""" cd $service_dir\n""")
        script_file.write(""" docker-compose -f docker-compose.yml pull\n""")
        script_file.write(""" docker-compose -f docker-compose.yml down\n""")
        script_file.write(""" docker-compose -f docker-compose.yml --env-file ./env/.env up -d\n""")
        script_file.write(""" cd ..\n}\n\n""")
        script_file.write("""# List of services to deploy\n""")
        script_file.write("services=({})\n\n".format(' '.join([f'\"{path}\"' for path in path_names])))
        script_file.write("""# Deploy each service\n""")
        script_file.write("""for service in "${services[@]}"; do\n""")
        script_file.write(""" deploy_service $service\n""")
        script_file.write("""done\n\n""")
        script_file.write("""# Clean up: Delete docker-compose.yml from eqm directory\n""")
        script_file.write("""rm docker-compose.yml\n""")


def confirm_variables(env_variables):
    print("Please review the entered variables:")
    for key, value in env_variables.items():
        if key.lower().find('password') != -1:
            print(f"{key}: {'*' * len(value)}")
        else:
            print(f"{key}: {value}")
    confirm = input("Are these variables correct? (yes/no): ").strip().lower()
    return confirm.startswith("y")


def main():
    try:
        path_names = input("Enter path names separated by commas: ").split(",")
        superuser_id = input("Enter superuser id: ")
        password = getpass.getpass(
            f"Enter {MYSQL_TEXT if '-p' not in sys.argv else POSTGRESQL_TEXT} password: ").strip()
        db_host = input("Enter database host: ").strip()
        db_port = input("Enter database port: ").strip()

        if "-p" in sys.argv:
            db_type = "postgresql"
        else:
            db_type = "mysql"

        if db_type == 'mysql':
            env_variables = OrderedDict([
                ("SUPERUSER_ID", superuser_id),
                ("DEVMODE", "false"),
                ("TZ", "Europe/Moscow"),
                ("MYSQL_USER", superuser_id),
                ("MYSQL_PASSWORD", password),
                ("MYSQL_ROOT_PASSWORD", password),
                ("DB_HOST", db_host),
                ("DB_PORT", db_port),
                ("MYSQL_DATABASE", superuser_id)
            ])
        elif db_type == 'postgresql':
            env_variables = OrderedDict([
                ("SUPERUSER_ID", superuser_id),
                ("DEVMODE", "false"),
                ("TZ", "Europe/Moscow"),
                ("POSTGRES_USER", superuser_id),
                ("POSTGRES_PASSWORD", password),
                ("POSTGRES_DB", superuser_id),
                ("DB_HOST", db_host),
                ("DB_PORT", db_port)
            ])
        else:
            print("Unsupported database type. Exiting.")
            return

        for path_name in path_names:
            telegram_bot_token = input(f"Enter TELEGRAM_BOT_TOKEN for {path_name}: ").strip()
            print("")
            env_variables["TELEGRAM_BOT_TOKEN"] = telegram_bot_token
            dir_name = path_name.strip()
            if not confirm_variables(env_variables):
                print("Please re-enter the variables.")
                return
            create_env_file(dir_name, env_variables)

        generate_script = input("Do you want to generate the deployment script? (yes/no): ").strip().lower()

        if generate_script.startswith("y"):
            generate_deploy_script(path_names)
            print("Deployment script generated: deploy_services.sh")
        else:
            print("No deployment script generated.")

    except KeyboardInterrupt:
        print("\nProcess interrupted. Exiting...")


if __name__ == "__main__":
    main()
