# 🧪 QUICK TEST GUIDE - DANH MỤC & KNOWLEDGE BASE

## 🚀 START HERE

### Server Status
```
✅ Running on: http://localhost:5000/
✅ Version: 2.0 Enhanced
✅ Categories: 10 danh mục
✅ Knowledge Base: 8 câu hỏi cố định
```

---

## 📂 TEST TẤT CẢ DANH MỤC

### 1️⃣ Electronics (Điện tử & Công nghệ)
```
URL: http://localhost:5000/category/Electronics
Expected:
  ✓ Tiêu đề: "Electronics"
  ✓ Mô tả: "Chuyên mục Electronics - Khám phá..."
  ✓ Hiển thị ~40+ sản phẩm
  ✓ Grid layout với product cards
```

### 2️⃣ Fashion (Thời trang)
```
URL: http://localhost:5000/category/Fashion
Expected:
  ✓ Tiêu đề: "Fashion"
  ✓ ~40+ sản phẩm thời trang
  ✓ Mỗi card: Tên, giá, rating, nút "Thêm vào giỏ"
```

### 3️⃣ Books (Sách)
```
URL: http://localhost:5000/category/Books
Expected:
  ✓ Danh mục sách với ~40+ sản phẩm
  ✓ Sidebar vẫn hiển thị tất cả danh mục
```

### 4️⃣ Clothing (Quần áo)
```
URL: http://localhost:5000/category/Clothing
Expected:
  ✓ Danh mục quần áo
```

### 5️⃣ Beauty (Làm đẹp)
```
URL: http://localhost:5000/category/Beauty
Expected:
  ✓ Sản phẩm mỹ phẩm & chăm sóc
```

### 6️⃣ Sports (Thể thao)
```
URL: http://localhost:5000/category/Sports
Expected:
  ✓ Dụng cụ thể thao
```

### 7️⃣ Home (Gia dụng)
```
URL: http://localhost:5000/category/Home
Expected:
  ✓ Đồ gia dụng, trang trí
```

### 8️⃣ Garden (Làm vườn)
```
URL: http://localhost:5000/category/Garden
Expected:
  ✓ Dụng cụ & sản phẩm làm vườn
```

### 9️⃣ Automotive (Ô tô)
```
URL: http://localhost:5000/category/Automotive
Expected:
  ✓ Phụ tùng & sản phẩm liên quan ô tô
```

### 🔟 Toys (Đồ chơi)
```
URL: http://localhost:5000/category/Toys
Expected:
  ✓ Đồ chơi & trò chơi
```

---

## 💬 TEST KNOWLEDGE BASE (8 CÂU HỎI)

### Test Bước:
1. Mở http://localhost:5000/
2. Scroll xuống góc dưới phải, tìm **Chat Widget**
3. Nhấp vào ô nhập tin nhắn
4. Gõ các câu hỏi dưới đây

---

### Question 1️⃣: "các danh mục sản phẩm là gì"

**Gõ vào chat:**
```
các danh mục sản phẩm là gì
```

**Kết quả dự kiến:**
```
✅ Bot trả lời (từ Knowledge Base):
"Chúng tôi có 10 danh mục sản phẩm chính:
1️⃣ Electronics - Điện tử, máy tính
2️⃣ Books - Sách, tài liệu
3️⃣ Clothing - Quần áo
4️⃣ Fashion - Thời trang
5️⃣ Beauty - Sản phẩm làm đẹp
6️⃣ Sports - Dụng cụ thể thao
7️⃣ Home - Đồ gia dụng
8️⃣ Garden - Dụng cụ làm vườn
9️⃣ Automotive - Phụ tùng ô tô
🔟 Toys - Đồ chơi

Bạn có thể click vào từng danh mục trên sidebar để xem đầy đủ sản phẩm."

❌ Không hiển thị sản phẩm (vì không cần)
✓ Trả lời từ Knowledge Base (không phải intent detection)
```

---

### Question 2️⃣: "sản phẩm tốt nhất là gì"

**Gõ vào chat:**
```
sản phẩm tốt nhất là gì
```

**Kết quả dự kiến:**
```
✅ Bot trả lời:
"Theo đánh giá của khách hàng, những sản phẩm bán chạy nhất 
và được yêu thích nhất là các sản phẩm trong danh mục 
Electronics và Books. Bạn có thể xem danh sách bán chạy 
bằng cách click vào 'Bán Chạy' trong menu lọc."

✅ Hiển thị: 5 sản phẩm bán chạy nhất
   ├─ Product XXX - 299,000₫
   ├─ Product YYY - 250,000₫
   ├─ Product ZZZ - 320,000₫
   └─ ...

✓ Trả lời từ Knowledge Base + kèm top products
```

---

### Question 3️⃣: "tôi nên mua sản phẩm nào"

**Gõ vào chat:**
```
tôi nên mua sản phẩm nào
```

**Kết quả dự kiến:**
```
✅ Bot trả lời:
"Hãy cho tôi biết bạn quan tâm đến danh mục nào? 
Chúng tôi có:
• Electronics - Điện tử & Công nghệ
• Books - Sách
• Clothing - Quần áo
• Fashion - Thời trang
• Beauty - Làm đẹp
• Sports - Thể thao
• Home - Gia dụng
• Garden - Làm vườn
• Automotive - Ô tô
• Toys - Đồ chơi"

❌ Không hiển thị sản phẩm (vì cần người dùng chọn danh mục)

✓ Trả lời từ Knowledge Base
```

---

### Question 4️⃣: "chiết khấu hoặc giảm giá"

**Gõ vào chat:**
```
chiết khấu hoặc giảm giá
```

**Kết quả dự kiến:**
```
✅ Bot trả lời:
"Hiện tại chúng tôi đang áp dụng chương trình giảm giá:
🎁 Giảm 10% cho đơn hàng đầu tiên
🎁 Miễn phí vận chuyển cho đơn hàng trên 500.000₫
🎁 Khách hàng trung thành được tích điểm

Hãy duyệt bộ sưu tập 'Giá Rẻ' của chúng tôi để tìm những sản phẩm giá tốt nhất!"

✅ Hiển thị: 5 sản phẩm giá rẻ nhất
   ├─ Product A - 100,000₫
   ├─ Product B - 105,000₫
   ├─ Product C - 110,000₫
   └─ ...

✓ Trả lời từ Knowledge Base + cheap products
```

---

### Question 5️⃣: "giao hàng mất bao lâu"

**Gõ vào chat:**
```
giao hàng mất bao lâu
```

**Kết quả dự kiến:**
```
✅ Bot trả lời:
"Thời gian giao hàng:
⏱️ Giao hàng standard: 5-7 ngày làm việc
⏱️ Giao hàng nhanh: 2-3 ngày làm việc (+50.000₫)
⏱️ Giao hàng trong ngày: Áp dụng tại các thành phố lớn (+100.000₫)

Ghi chú: Hàng sẽ được đóng gói cẩn thận và bảo hiểm miễn phí."

❌ Không hiển thị sản phẩm

✓ Trả lời từ Knowledge Base (chỉ thông tin, không cần products)
```

---

### Question 6️⃣: "chính sách đổi trả như thế nào"

**Gõ vào chat:**
```
chính sách đổi trả như thế nào
```

**Kết quả dự kiến:**
```
✅ Bot trả lời:
"Chính sách đổi trả của chúng tôi:
✅ Đổi/trả trong 30 ngày nếu sản phẩm lỗi
✅ Đổi/trả trong 7 ngày nếu không hài lòng
✅ Hoàn tiền 100% nếu không cần sản phẩm
✅ Vận chuyển trả hàng MIỄN PHÍ

Liên hệ với chúng tôi để được hỗ trợ chi tiết!"

❌ Không hiển thị sản phẩm

✓ Trả lời từ Knowledge Base
```

---

### Question 7️⃣: "thanh toán bằng cách nào"

**Gõ vào chat:**
```
thanh toán bằng cách nào
```

**Kết quả dự kiến:**
```
✅ Bot trả lời:
"Phương thức thanh toán:
💳 Thẻ tín dụng/ghi nợ (Visa, Mastercard)
🏦 Chuyển khoản ngân hàng
📱 Ví điện tử (Momo, ZaloPay)
💵 Tiền mặt khi nhận hàng (COD)

Tất cả giao dịch được bảo mật bằng SSL 256-bit."

❌ Không hiển thị sản phẩm

✓ Trả lời từ Knowledge Base
```

---

### Question 8️⃣: "sản phẩm này có bao nhiêu trong kho"

**Gõ vào chat:**
```
sản phẩm này có bao nhiêu trong kho
```

**Kết quả dự kiến:**
```
✅ Bot trả lời:
"Tất cả các sản phẩm trên website của chúng tôi đều còn hàng 
và sẵn sàng giao ngay. Bạn có thể thêm vào giỏ 
và thanh toán bất kỳ lúc nào!"

❌ Không hiển thị sản phẩm

✓ Trả lời từ Knowledge Base
```

---

## 🔍 TEST INTENT DETECTION (Fallback)

Nếu câu hỏi **KHÔNG** trong Knowledge Base:

### Test 1: "recommend sản phẩm cho tôi"

**Gõ vào chat:**
```
recommend sản phẩm cho tôi
```

**Kết quả dự kiến:**
```
✅ Không match KB → Intent Detection
✅ Intent: "recommend"
✅ Bot trả lời:
   "Dựa trên lịch sử mua hàng của bạn, đây là những sản phẩm được gợi ý:"

✅ Hiển thị: 5 sản phẩm từ lịch sử người dùng
   ├─ Product A - 199,000₫
   ├─ Product B - 249,000₫
   ├─ Product C - 299,000₫
   └─ ...
```

---

### Test 2: "tôi muốn sản phẩm giá rẻ"

**Gõ vào chat:**
```
tôi muốn sản phẩm giá rẻ
```

**Kết quả dự kiến:**
```
✅ Không match KB → Intent Detection
✅ Intent: "cheap"
✅ Bot trả lời:
   "Những sản phẩm giá tốt cho bạn:"

✅ Hiển thị: 5 sản phẩm giá rẻ nhất
   ├─ Product X - 100,000₫
   ├─ Product Y - 105,000₫
   └─ ...
```

---

### Test 3: "show me electronics"

**Gõ vào chat:**
```
show me electronics
```

**Kết quả dự kiến:**
```
✅ Không match KB → Intent Detection
✅ Intent: "category"
✅ Bot trả lời:
   "Sản phẩm trong danh mục này:"

✅ Hiển thị: 5 sản phẩm từ category Electronics
```

---

## 🛒 TEST ADD TO CART

### From Chat:
```
1. Bot hiển thị sản phẩm trong chat
2. Click vào sản phẩm
3. Chat shows: "✅ Sản phẩm P123 đã được thêm vào giỏ hàng!"
```

### From Category Page:
```
1. Vào danh mục (ví dụ: Electronics)
2. Click nút "🛒 Thêm vào giỏ" trên product card
3. Chat widget shows confirmation
```

---

## ✅ CHECKLIST

### Danh Mục (Mark when tested)
- [ ] Electronics - http://localhost:5000/category/Electronics
- [ ] Fashion - http://localhost:5000/category/Fashion
- [ ] Books - http://localhost:5000/category/Books
- [ ] Clothing - http://localhost:5000/category/Clothing
- [ ] Beauty - http://localhost:5000/category/Beauty
- [ ] Sports - http://localhost:5000/category/Sports
- [ ] Home - http://localhost:5000/category/Home
- [ ] Garden - http://localhost:5000/category/Garden
- [ ] Automotive - http://localhost:5000/category/Automotive
- [ ] Toys - http://localhost:5000/category/Toys

### Knowledge Base Questions (Mark when tested)
- [ ] "các danh mục sản phẩm là gì"
- [ ] "sản phẩm tốt nhất là gì"
- [ ] "tôi nên mua sản phẩm nào"
- [ ] "chiết khấu hoặc giảm giá"
- [ ] "giao hàng mất bao lâu"
- [ ] "chính sách đổi trả như thế nào"
- [ ] "thanh toán bằng cách nào"
- [ ] "sản phẩm này có bao nhiêu trong kho"

### Intent Detection (Mark when tested)
- [ ] "recommend sản phẩm cho tôi"
- [ ] "tôi muốn sản phẩm giá rẻ"
- [ ] "show me electronics"

### Other Features
- [ ] Add to cart from chat
- [ ] Add to cart from category page
- [ ] Search functionality
- [ ] Sidebar navigation

---

## 🎯 EXPECTED OUTCOMES

**All Tests Pass If:**

✅ Danh mục pages hiển thị chính xác  
✅ Knowledge Base câu hỏi trả lời từ fixed answers  
✅ Sản phẩm hiển thị khi cần  
✅ Sản phẩm không hiển thị khi không cần  
✅ Intent detection fallback hoạt động  
✅ Add to cart hoạt động  

---

## 🔧 TROUBLESHOOTING

### Danh mục không hiển thị?
```bash
# Check URL format
http://localhost:5000/category/Electronics
# Not: http://localhost:5000/category/electronics (case sensitive)

# Try another category
http://localhost:5000/category/Fashion
```

### Chat không hiển thị?
```bash
# Check browser console (F12)
# Verify POST to /api/chat works

# Try a simple question
"hello"

# Try a KB question
"các danh mục sản phẩm là gì"
```

### Sản phẩm không hiển thị?
```bash
# Some KB questions DON'T show products
# Expected behavior for:
  ✓ "các danh mục sản phẩm là gì" → No products
  ✓ "thanh toán bằng cách nào" → No products
  ✓ "giao hàng mất bao lâu" → No products

# These SHOULD show products:
  ✓ "sản phẩm tốt nhất là gì" → Top 5
  ✓ "chiết khấu hoặc giảm giá" → 5 Cheap
```

---

**Ready to test? Start here:**
```
1. Open: http://localhost:5000/
2. Click category in sidebar
3. Or send message in chat widget
4. Expected: See products or KB answers
```

🎉 **Happy testing!**
