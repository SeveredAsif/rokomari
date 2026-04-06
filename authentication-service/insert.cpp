#include <bits/stdc++.h>
using namespace std;

int main() {
    ofstream file("temp.sql");

    if (!file.is_open()) {
        cout << "Error opening file!\n";
        return 1;
    }

    int N = 1000;

    for (int i = 1; i <= N; i++) {
        file<<"UPDATE products SET image_url = '' WHERE product_id = "<<i<<";\n";
    }

    // ---------------- USERS ----------------
    // file << "-- USERS\n";
    // for (int i = 1; i <= N; i++) {
    //     file << "INSERT INTO users (full_name, email, phone, password_hash) VALUES (";
    //     file << "'User " << i << "', ";
    //     file << "'user" << i << "@mail.com', ";
    //     file << "'017" << setw(8) << setfill('0') << i << "', ";
    //     file << "'hash" << i << "');\n";
    // }

    // // ---------------- ADMINS ----------------
    // file << "\n-- ADMINS\n";
    // for (int i = 1; i <= 10; i++) {
    //     file << "INSERT INTO admins (user_id) VALUES (" << i << ");\n";
    // }

    // // ---------------- CATEGORIES ----------------
    // file << "\n-- CATEGORIES\n";
    // vector<string> categories = {"Books", "Stationery", "Electronics", "Gifts", "Others"};
    // for (auto &c : categories) {
    //     file << "INSERT INTO categories (category_name) VALUES ('" << c << "');\n";
    // }

    // // ---------------- PRODUCTS ----------------
    // file << "\n-- PRODUCTS\n";
    // vector<string> types = {"BOOK", "STATIONERY", "ELECTRONICS", "GIFT", "OTHER"};

    // srand(time(0));

    // for (int i = 1; i <= N; i++) {
    //     int cat = rand() % 5 + 1;
    //     double price = (rand() % 1000) + 50;
    //     int stock = rand() % 100;
    //     string type = types[rand() % 5];

    //     file << "INSERT INTO products (product_name, category_id, price, stock_qty, brand, product_type) VALUES (";
    //     file << "'Product " << i << "', ";
    //     file << cat << ", ";
    //     file << fixed << setprecision(2) << price << ", ";
    //     file << stock << ", ";
    //     file << "'Brand " << (i % 10 + 1) << "', ";
    //     file << "'" << type << "');\n";
    // }

    // // ---------------- ADDRESSES ----------------
    // file << "\n-- ADDRESSES\n";
    // for (int i = 1; i <= N; i++) {
    //     file << "INSERT INTO addresses (user_id, recipient_name, phone, address_line, city, area, postal_code) VALUES (";
    //     file << i << ", ";
    //     file << "'User " << i << "', ";
    //     file << "'017" << setw(8) << setfill('0') << i << "', ";
    //     file << "'Address " << i << "', ";
    //     file << "'City " << (i % 5 + 1) << "', ";
    //     file << "'Area " << (i % 10 + 1) << "', ";
    //     file << "'100" << i << "');\n";
    // }

    // // ---------------- CART ----------------
    // file << "\n-- CART\n";
    // for (int i = 1; i <= N; i++) {
    //     file << "INSERT INTO cart (user_id) VALUES (" << i << ");\n";
    // }

    // // ---------------- ORDERS ----------------
    // file << "\n-- ORDERS\n";
    // vector<string> orderStatus = {"PENDING","CONFIRMED","PACKED","SHIPPED","DELIVERED"};

    // for (int i = 1; i <= N; i++) {
    //     double total = (rand() % 5000) + 100;

    //     file << "INSERT INTO orders (user_id, address_id, total_amount, shipping_charge, discount_amount, order_status) VALUES (";
    //     file << (rand()%N + 1) << ", ";
    //     file << (rand()%N + 1) << ", ";
    //     file << fixed << setprecision(2) << total << ", ";
    //     file << (rand()%100) << ", ";
    //     file << (rand()%50) << ", ";
    //     file << "'" << orderStatus[rand()%5] << "');\n";
    // }

    // // ---------------- PAYMENTS ----------------
    // file << "\n-- PAYMENTS\n";
    // vector<string> methods = {"COD","BKASH","NAGAD","CARD"};
    // vector<string> payStatus = {"UNPAID","PAID","FAILED"};

    // for (int i = 1; i <= N; i++) {
    //     file << "INSERT INTO payments (order_id, payment_method, payment_status, transaction_id, paid_at) VALUES (";
    //     file << i << ", ";
    //     file << "'" << methods[rand()%4] << "', ";
    //     file << "'" << payStatus[rand()%3] << "', ";
    //     file << "'TXN" << i << "', ";
    //     file << "CURRENT_TIMESTAMP);\n";
    // }

    file.close();
    cout << "SQL file generated: bulk_insert.sql\n";

    return 0;
}