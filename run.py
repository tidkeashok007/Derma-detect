from app import create_app
from app.utils.seed import seed_users

# Create an instance of the Flask app
app = create_app()

def main():
    # Seed the database
    with app.app_context():
        seed_users()
        
    print("Database seeded successfully.")

    # Run the app in debug mode
    app.run(debug=True)

if __name__ == '__main__':
    main()
