from flask import Flask, abort, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text, desc
import os
from datetime import datetime
now = datetime.now()

from werkzeug.utils import secure_filename

# Initialize Flask app
app = Flask(__name__)

# Configure SQLAlchemy to use SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///skeletor.db'

# Define the upload folder for product images
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')

# Define allowed file extensions for product images
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Define the products table model
class products(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    cr_price = db.Column(db.Integer, nullable=False)
    am_price = db.Column(db.Integer, nullable=False)
    first_cr_price = db.Column(db.Integer, nullable=False)
    second_cr_price = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    product_model = db.Column(db.String(50), nullable=False)
    amt_sold = db.Column(db.Integer, nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    brand = db.Column(db.String(50), nullable=False)
    what_in_box = db.Column(db.String(50), nullable=False)
    seller_name = db.Column(db.String(50), nullable=False)
    product_rating = db.Column(db.Integer, nullable=False)
    product_rating_count = db.Column(db.Integer, nullable=False)
    image = db.Column(db.String(50), nullable=False)
    product_images = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(50), nullable=False)
    shelf_life = db.Column(db.Integer, nullable=False)
    date_added = db.Column(db.String(50), nullable=False)



# Define route for the home page
@app.route('/')
def home():
    return render_template('home.html')

# Define route for displaying products in the store
@app.route('/store')
def store():
    # Commit any pending database changes
    db.session.commit()
    # Retrieve all products from the database
    products_list = products.query.order_by(desc(products.amt_sold)).all()
    # Render the store template with the list of products
    return render_template('store.html', products=products_list)

# Define route for displaying a single product
@app.route('/product/<int:id>')
def product(id):
    # Retrieve the product with the given id from the database
    product = products.query.get(id)
    # Split the product images string into a list of filenames
    product_images = product.product_images.split(',')
    # Check if the product exists
    if product is None:
        abort(404)  # Not found
    # Render the product template with the product details and images
    return render_template('product.html', product=product, product_images=product_images)

# Function to check if a file has an allowed extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Define route for adding a new product
@app.route('/addproduct', methods=['GET', 'POST'])
def addproduct():
    if request.method == 'POST':
        # Check if the request contains any files
        if 'images' not in request.files:
            flash('No file part')
            return redirect(request.url)
        # Get the list of files uploaded
        files = request.files.getlist('images')
        filenames = []
        # Iterate over the uploaded files
        for file in files:
            # Check if the file is valid
            if file and allowed_file(file.filename):
                # Securely save the file to the upload folder
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                filenames.append(filename)
        # Extract product details from the form
        name = request.form['name']
        am_price = int(request.form['am_price'])
        first_cr_price = int(request.form['first_cr_price'])
        second_cr_price = int(request.form['second_cr_price'])
        amt_sold = int(request.form['amt_sold'])
        stock = int(request.form['stock'])
        brand = request.form['product_brand']
        what_in_box = request.form['what_in_box']
        seller_name = request.form['seller_name']
        product_rating = int(request.form['product_rating'])
        product_rating_count = int(request.form['product_rating_count'])
        current_month = now.month
        current_year = now.year
        date_added = f"{current_month}/{current_year}"   
        category = request.form['category']
        product_model = request.form['product_model']
        shelf_life = request.form['shelf_life']
        description = request.form['description']
        # Concatenate uploaded image filenames into a string
        product_images = ','.join(filenames)
        # Create a new product object
        product = products(name=name, cr_price=((am_price+first_cr_price+second_cr_price)/3), am_price=am_price, first_cr_price=first_cr_price, second_cr_price=second_cr_price, image=filenames[0], product_images=product_images, description=description, amt_sold=amt_sold, stock=stock, brand=brand, what_in_box=what_in_box, seller_name=seller_name, product_rating=product_rating, date_added=date_added, shelf_life=shelf_life, product_rating_count=product_rating_count ,category=category, product_model=product_model)        
        # Add the new product to the database session
        db.session.add(product)
        # Commit the changes to the database
        db.session.commit()
        # Redirect to the store page
        return redirect(url_for('store'))
    # Render the addproduct template for GET requests
    return render_template('addproduct.html')


@app.route('/admin_home')
def admin_home():
    # Commit any pending database changes
    db.session.commit()
    # Retrieve all products from the database
    products_list = products.query.order_by(desc(products.amt_sold)).all()

    # Render the store template with the list of products
    return render_template('admin_home.html', products=products_list)


@app.route('/analytics/<int:id>')
def analytics(id):
    product = products.query.get(id)
    if product is None:
        abort(404)
    return render_template('analytics.html', product=product)

#Define triggers to update cr_price after insert and update operations

with app.app_context():
    with db.engine.connect() as connection:
        connection.execute(text("""
        CREATE TRIGGER IF NOT EXISTS calculate_cr_price_insert
        AFTER INSERT ON products
        FOR EACH ROW
        BEGIN
          UPDATE products
          SET cr_price = (NEW.am_price + NEW.first_cr_price + NEW.second_cr_price) / 3
          WHERE id = NEW.id;
        END;
        """))

        connection.execute(text("""
        CREATE TRIGGER IF NOT EXISTS calculate_cr_price_update
        AFTER UPDATE ON products
        FOR EACH ROW
        BEGIN
          UPDATE products
          SET cr_price = MAX(NEW.am_price, ((NEW.am_price + NEW.first_cr_price + NEW.second_cr_price) / 3) * (1 - NEW.stock * 0.05))
          WHERE id = NEW.id;
        END;
        """))

       
      

# Run the Flask application
if __name__ == '__main__':
    app.run(debug=True, port=8000, host='0.0.0.0')
