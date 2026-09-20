# � Always Stay Hydrated

Web học Khải Huyền mang phong cách học tập hiện đại, trực quan và dễ duy trì hàng ngày. Dự án tập trung vào việc giúp người học tiếp cận Kinh Thánh theo nhiều hình thức khác nhau như đọc, điền từ, luyện gõ, flashcard, làm bài kiểm tra và theo dõi tiến độ một cách khoa học.

> Mục tiêu của dự án là kết hợp giữa học nội dung Kinh Thánh và hình thành thói quen học tập bền vững: lặp lại, ôn tập, nhắc nhở và đo lường tiến độ.

---

## 1. Tổng quan dự án

Always Stay Hydrated là một ứng dụng web học Khải Huyền được xây dựng bằng Flask, giúp người dùng:

- đọc Kinh Thánh theo sách và chương
- luyện điền từ vào câu Kinh Thánh
- luyện gõ mười ngón dựa trên các câu kinh
- học bằng flashcard 3 mặt: tiêu đề, trích đoạn và giải nghĩa
- theo dõi tiến độ học tập và lịch ôn tập
- làm bài kiểm tra theo từng phần học
- tham gia thách đấu trực tiếp và xem bảng xếp hạng

Dự án không chỉ là một website học Kinh Thánh đơn thuần, mà còn là một nền tảng học tập cá nhân có cấu trúc, nhắc nhở định kỳ và hệ thống tiến độ rõ ràng.

---

## 2. Tính năng chính

### 2.1 Điền vào chỗ trống

Người học sẽ được đưa ra các câu Kinh Thánh có từ hoặc cụm từ bị ẩn. Nhiệm vụ là điền đúng phần thiếu để củng cố trí nhớ và hiểu ý nghĩa câu nói.

- giúp ghi nhớ câu văn chính xác hơn
- tăng khả năng nhận diện và suy luận ý nghĩa
- phù hợp cho việc học nhẩm và ôn tập hàng ngày

### 2.2 Luyện gõ mười ngón

Tính năng này cho phép người dùng gõ lại các câu Kinh Thánh theo đúng văn bản gốc. Hệ thống có thể đo:

- tốc độ gõ (WPM)
- độ chính xác
- số lỗi
- tiến độ luyện tập

Đây là dạng học kết hợp giữa đọc, nhớ và kỹ năng thao tác, rất phù hợp với người muốn tăng sự tập trung và khả năng tiếp thu lời Chúa.

### 2.3 Flashcard 3 mặt

Flashcard là tính năng học từ vựng và tri thức theo kiểu lặp lại có chủ đích.

Mỗi thẻ có 3 mặt:

1. Tiêu đề
2. Trích đoạn / câu dẫn
3. Giải nghĩa / hướng dẫn hiểu

Người dùng có thể:

- xem tiến độ học tập
- đánh dấu những phần cần ôn lại
- sắp xếp theo danh mục hoặc mức độ
- học theo lịch nhắc lại hợp lý

Mật khẩu truy cập vào khu vực flashcard: `dongan`

### 2.4 Kiểm tra đóng ấn và hệ thống học phần

Dự án có chế độ kiểm tra theo từng học phần với cơ chế bảo mật và quản lý tiến độ rõ ràng:

- mỗi học phần có mật khẩu riêng do admin cấp
- bài kiểm tra được gửi xuống theo từng mục riêng
- toàn bộ học phần sẽ được xoá sau khoảng 2 tuần nếu cần làm mới dữ liệu
- hệ thống ghi nhận thành tích và huy hiệu sau khi hoàn thành bài kiểm tra

Điều này giúp mô hình học tập có tính kiểm soát, phù hợp cho môi trường học nhóm, lớp học hoặc người quản lý nội dung.

### 2.5 Nhiệm vụ hàng ngày

Một trong những điểm nổi bật của phiên bản mới là hệ thống “Nhiệm vụ hôm nay”.

- mỗi ngày xuất hiện 5 nhiệm vụ cố định
- người học có thể theo dõi thói quen học tập đều đặn
- giúp tạo động lực và sự ổn định mỗi ngày
- hỗ trợ tiến độ học tập rõ ràng hơn

### 2.6 Dòng chảy ứng nghiệm Khải Huyền

Ứng dụng cung cấp timeline các mốc ứng nghiệm Khải Huyền, được sắp xếp theo tiến trình:

- Bỏ đạo
- Hủy diệt
- Cứu rỗi

Điều này giúp người học hình dung rõ tiến trình lịch sử và mối liên hệ giữa các sự kiện quan trọng trong Khải Huyền.

### 2.7 Đọc Kinh Thánh

Có giao diện đọc sách chuyên biệt, cho phép người học:

- chọn sách và chương
- đọc theo từng chương rõ ràng
- tập trung vào văn bản mà không bị rối bởi layout phức tạp
- dễ xem và duyệt theo danh sách chương

### 2.8 Đấu trường Khải Huyền

Tính năng thi đấu trực tiếp cho phép:

- đối đầu cùng bạn bè
- trả lời các câu hỏi về Khải Huyền
- theo dõi bảng xếp hạng
- thúc đẩy sự cạnh tranh lành mạnh trong học tập

---

## 3. Cập nhật mới nổi bật

### BIG UPDATE 1.0.0

Phiên bản mới của dự án mang đến nhiều cải tiến đáng kể:

#### Giao diện hoàn toàn mới

- thiết kế tối giản, hiện đại
- dễ nhìn hơn trên máy tính lẫn điện thoại
- thân thiện với người dùng và dễ điều hướng

#### Nhiệm vụ hôm nay

- hệ thống nhắc nhở việc học mỗi ngày
- duy trì thói quen học đều đặn
- tạo cảm giác hoàn thành và tiến bộ liên tục

#### Dòng chảy ứng nghiệm Khải Huyền

- trình bày tiến độ ứng nghiệm theo lộ trình logic
- giúp người học hiểu rõ mối liên hệ giữa các sự kiện

#### Đọc Kinh Thánh

- giao diện tập trung hơn
- trải nghiệm đọc thư giãn, dễ tiếp cận
- phù hợp cho việc đọc và suy ngẫm lâu hơn

---

## 4. Công nghệ sử dụng

Dự án hiện đang triển khai trên nền tảng web bằng các công nghệ chính sau:

- Python
- Flask
- SQLAlchemy
- SQLite / PostgreSQL
- Jinja2 Templates
- Flask-SocketIO
- Argon2 password hashing
- HTML / CSS / JavaScript

Ngoài ra, dự án hỗ trợ:

- tích hợp dữ liệu Kinh Thánh từ file JSON
- lưu tiến độ người dùng vào database
- hỗ trợ deploy trên Render hoặc môi trường server khác

---

## 5. Cấu trúc dự án

```text
ASH/
├── README.md
├── Project.pdf
├── Project_PNG/
├── TTF_Fonts/
├── encode_images.py
├── extract_docx.py
├── flashcard_js_check.js
├── test_api_now.py
├── AlwayStayHydrated/
│   ├── app.py
│   ├── flashcard_models.py
│   ├── init_db.py
│   ├── init_flashcard_db.py
│   ├── multiplayer.py
│   ├── khai_huyen_data.json
│   ├── timeline_data.json
│   ├── users.json
│   ├── requirements.txt
│   ├── Procfile
│   ├── static/
│   ├── templates/
│   └── instance/
└── .venv/
```

Các folder quan trọng:

- `AlwayStayHydrated/app.py`: file chính của ứng dụng Flask
- `AlwayStayHydrated/templates/`: giao diện người dùng
- `AlwayStayHydrated/static/`: file CSS, JS, hình ảnh
- `AlwayStayHydrated/khai_huyen_data.json`: dữ liệu Kinh Thánh
- `AlwayStayHydrated/flashcard_models.py`: model dữ liệu flashcard và người dùng

---

## 6. Cách chạy dự án ở local

### 6.1 Yêu cầu

- Python 3.10+
- pip
- môi trường ảo (khuyến nghị)

### 6.2 Tạo môi trường ảo

```bash
cd AlwayStayHydrated
python -m venv .venv
.venv\Scripts\activate
```

### 6.3 Cài đặt phụ thuộc

```bash
pip install -r requirements.txt
```

### 6.4 Chạy ứng dụng

```bash
python app.py
```

Mặc định ứng dụng sẽ chạy ở địa chỉ:

```text
http://localhost:5000
```

---

## 7. Cấu hình deploy và database

Dự án hỗ trợ chạy cả trên SQLite local và PostgreSQL khi deploy lên Render hoặc hosting tương tự.

### Môi trường local

- nếu không có `DATABASE_URL`, hệ thống sẽ dùng SQLite mặc định
- file cơ sở dữ liệu sẽ được lưu trong thư mục `instance/`

### Môi trường deploy

Khi deploy trên Render hoặc dịch vụ tương tự, nên cấu hình các biến môi trường sau:

```bash
DATABASE_URL=postgresql://...
SECRET_KEY=your-very-long-random-secret
SQLITE_DATABASE_PATH=instance/flashcard.db
```

Lưu ý:

- khi `DATABASE_URL` được cung cấp, ứng dụng ưu tiên PostgreSQL
- `SECRET_KEY` nên được đặt cố định để bảo mật session và token
- nếu có dữ liệu cũ trong `users.json`, ứng dụng sẽ tự import vào database khi bảng `users` đang trống

---

## 8. Quy trình người dùng

Một người dùng có thể trải nghiệm dự án theo các bước sau:

1. Đăng nhập / đăng ký tài khoản
2. Truy cập giao diện chính
3. Chọn chức năng học tập phù hợp:
   - đọc Kinh Thánh
   - điền từ
   - luyện gõ
   - flashcard
   - timeline
   - bài kiểm tra
4. Theo dõi tiến độ và ôn lại theo lịch
5. Tham gia luyện tập hàng ngày để duy trì thói quen

---

## 9. Đặc điểm nổi bật của sản phẩm

- học theo lộ trình và nhắc lại hàng ngày
- tích hợp nhiều dạng học tập trong một nền tảng
- phù hợp cho việc học cá nhân và học nhóm
- dễ triển khai, bảo trì và mở rộng tính năng
- hướng tới trải nghiệm học tập vừa có tính giáo dục, vừa có tính hứng thú

---

## 10. Demo / liên kết

Dự án hiện có thể trải nghiệm qua môi trường deploy demo như:

- `alwaysstayhydrated.onrender.com`

> Lưu ý: đường dẫn demo có thể thay đổi tùy thời điểm deploy hoặc cấu hình môi trường.

---

## 11. Tình trạng dự án

Dự án đang ở giai đoạn tích hợp và hoàn thiện các tính năng học tập chính, với các module cốt lõi đã được xây dựng và sẵn sàng dùng để học tập, luyện tập và theo dõi tiến độ.

Các điểm mạnh hiện tại:

- giao diện học tập mới, hiện đại hơn
- chức năng đọc, flashcard, điền từ, luyện gõ
- hệ thống nhiệm vụ hàng ngày
- timeline ứng nghiệm
- kiểm tra / thành tích / hệ thống người dùng

---

## 12. Kết luận

Always Stay Hydrated không chỉ là một website học Khải Huyền thông thường, mà là một nền tảng học tập tương tác, có tính lặp lại, nhắc nhở và theo dõi tiến độ rõ ràng. Với cách tiếp cận kết hợp giữa Kinh Thánh, thực hành, ôn tập và sự cạnh tranh lành mạnh, dự án mang lại trải nghiệm học tập sâu sắc và bền vững hơn.

Nếu bạn đang muốn phát triển tiếp dự án, đây là một nền tảng rất phù hợp để mở rộng thêm:

- khóa học theo từng cấp độ
- hệ thống điểm thưởng và huy hiệu
- bảng xếp hạng cộng đồng
- quản lý admin nâng cao
- tích hợp nội dung mới theo từng giai đoạn giảng dạy

---
