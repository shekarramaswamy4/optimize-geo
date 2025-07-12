// MongoDB initialization script

// Switch to admin database to authenticate
db = db.getSiblingDB('admin');
db.auth('admin', 'admin_password');

// Switch to lumarank database
db = db.getSiblingDB('lumarank');

// Create a user for the application
db.createUser({
  user: 'lumarank_user',
  pwd: 'lumarank_password',
  roles: [
    {
      role: 'readWrite',
      db: 'lumarank'
    }
  ]
});

// Create collections
db.createCollection('website_crawl_data');

// Create indexes for website_crawl_data collection
db.website_crawl_data.createIndex({ 'website_url': 1 }, { unique: true });
db.website_crawl_data.createIndex({ 'domain': 1 });
db.website_crawl_data.createIndex({ 'crawl_status': 1 });
db.website_crawl_data.createIndex({ 'created_at': -1, 'crawl_status': 1 });
db.website_crawl_data.createIndex({ 
  'company_name': 'text', 
  'page_title': 'text', 
  'meta_description': 'text' 
});

print('MongoDB initialization completed');