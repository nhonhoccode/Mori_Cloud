# Mori_Cloud

**Mori_Cloud** là một nền tảng web giúp người dùng lưu giữ, quản lý và chia sẻ các khoảnh khắc đáng nhớ dưới dạng hình ảnh và văn bản. Ứng dụng tích hợp trí tuệ nhân tạo để hỗ trợ tìm kiếm ảnh thông minh, đồng thời mang đến trải nghiệm tương tác cộng đồng hiện đại và an toàn.

---
## Mô tả đề tài
### 1. Mô tả tổng quan

Trong cuộc sống hiện đại, nhu cầu lưu giữ và chia sẻ những khoảnh khắc ý nghĩa ngày càng trở nên thiết yếu. 

Tuy nhiên, việc quản lý và truy xuất các kỷ niệm (dưới dạng ảnh, văn bản) thường gặp khó khăn do thiếu công cụ hỗ trợ hiệu quả, thông minh và cá nhân hóa. Đề tài “Xây dựng ứng dụng website giúp mọi người lưu giữ kỷ niệm” ra đời nhằm giải quyết vấn đề đó bằng cách phát triển một nền tảng web thân thiện, hiện đại và tích hợp công nghệ AI.

Ý tưởng chính là xây dựng một hệ thống cho phép người dùng lưu trữ, tổ chức, tìm kiếm và tương tác với các kỷ niệm của mình thông qua hình ảnh và mô tả văn bản. Ứng dụng sử dụng mô hình học sâu OpenCLIP (ViT-L-14) để trích xuất đặc trưng từ ảnh và văn bản, kết hợp với FAISS nhằm tìm kiếm các ảnh tương đồng một cách nhanh chóng. Hệ thống còn hỗ trợ các tính năng cộng đồng như thích, bình luận, chia sẻ, đồng thời đảm bảo bảo mật với Knox token và hỗ trợ đăng nhập qua Google OAuth.

Lý do chọn đề tài xuất phát từ thực tiễn rằng hầu hết các nền tảng chia sẻ hiện nay đều thiên về mạng xã hội chung chung, thiếu đi khả năng tổ chức và truy xuất các kỷ niệm theo ngữ cảnh cá nhân hóa. Đề tài kỳ vọng sẽ góp phần lấp đầy khoảng trống này bằng một giải pháp vừa tiện ích vừa thông minh.

### 2. Mục tiêu
Đề tài hướng đến các mục tiêu cụ thể sau:
- Xây dựng một nền tảng web cho phép người dùng lưu trữ, quản lý và chia sẻ các khoảnh khắc cá nhân một cách trực quan, hiệu quả.
- Tích hợp mô hình AI OpenCLIP để trích xuất đặc trưng ảnh và văn bản, đồng thời sử dụng FAISS cho tìm kiếm ảnh thông minh bằng văn bản hoặc ảnh tương tự.
- Phát triển giao diện người dùng thân thiện, hỗ trợ đầy đủ chức năng như quản lý ảnh, album, thùng rác, lịch sử tìm kiếm và tương tác cộng đồng (like, comment).
- Áp dụng các cơ chế xác thực bảo mật (Knox Token, OAuth 2.0), đảm bảo an toàn và quyền riêng tư cho người dùng.
- Xây dựng hệ thống phân quyền và quản trị nội dung giúp admin giám sát và điều phối nền tảng hiệu quả.
---

## Thông tin nhóm

* **Trần Xuân Diện** – MSSV: 22650601
* **Nguyễn Đăng Tuấn Huy** – MSSV: 22658341
* **Võ Trọng Nhơn** – MSSV: 22658441    
* **Đỗ Tấn Đạt** – MSSV: 22648601
* **Trần Phú Thọ** – MSSV: 22653431

---

## Cài đặt và chạy ứng dụng

### Yêu cầu hệ thống

* Python 3.8 trở lên
* Git
* Docker (nếu chạy bằng container)

### Hướng dẫn cài đặt thủ công (Local)

1. **Clone repository**

```bash
git clone https://github.com/xndien2004/Mori_Cloud.git
cd Mori_Cloud/mori
```

2. **Tạo và kích hoạt môi trường ảo**

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

3. **Cài đặt thư viện**

```bash
pip install -r requirements.txt
```

4. **Thực hiện migration**

```bash
python manage.py makemigrations
python manage.py migrate
```

5. **Chạy server**

```bash
python manage.py runserver
```

Truy cập tại: `http://localhost:8000`

---

### Hướng dẫn chạy bằng Docker

```bash
docker compose down -v
docker volume prune -f 
docker compose up -d --build
```

---

## Video demo
- Xem video demo ứng dụng tại: [Video Demo](https://drive.google.com/file/d/1Na6xqTnkFOgA56y_bOgjq7zBqYWO2WbP/view?usp=sharing)

---

## Screenshots

### 1. Các giao diện chính: Đăng nhập, Đăng ký, Landing Page, Quên mật khẩu, Trang cá nhân

<table>
  <tr>
    <td align="center">
      <img src="./images/landing_pages.jpg" width="250px"><br>
      <em>Landing Page</em>
    </td>
    <td align="center">
      <img src="./images/login.jpg" width="250px"><br>
      <em>Đăng nhập</em>
    </td>
    <td align="center">
      <img src="./images/register.jpg" width="250px"><br>
      <em>Đăng ký</em>
    </td>
  </tr>
  <tr>
    <td align="center">
      <img src="./images/quen_mat_khau.jpg" width="250px"><br>
      <em>Quên mật khẩu</em>
    </td>
    <td align="center">
      <img src="./images/trang_ca_nhan.jpg" width="250px"><br>
      <em>Trang cá nhân</em>
    </td>
  </tr>
</table>

---

### 2. Tổng quan trang chủ

<div align="center">
  <img src="./images/home_after_login.jpg" width="90%"><br>
  <em style="color: gray;">Trang chủ sau khi đăng nhập</em>
</div>

---

### 3. Quản lý ảnh

<table>
  <tr>
    <td align="center">
      <img src="./images/quan_ly_album_vs_anh.jpg" width="300px"><br>
      <em>Tổng quan ảnh và album</em>
    </td>
    <td align="center">
      <img src="./images/quan_ly_anh.jpg" width="300px"><br>
      <em>Giao diện quản lý ảnh</em>
    </td>
  </tr>
</table>

---

### 4. Quản lý album

<table>
  <tr>
    <td align="center">
      <img src="./images/quan_ly_album.jpg" width="300px"><br>
      <em>Danh sách album</em>
    </td>
    <td align="center">
      <img src="./images/quan_ly_album_tao_album.jpg" width="300px"><br>
      <em>Tạo album mới</em>
    </td>
  </tr>
</table>

---

### 5. Quản lý thùng rác

<div align="center">
  <img src="./images/thung_rac.jpg" width="90%"><br>
  <em style="color: gray;">Thùng rác – quản lý ảnh đã xóa</em>
</div>

---

### 6. Tìm kiếm thông thường/AI, quản lý lịch sử tìm kiếm

<table>
  <tr>
    <td align="center">
      <img src="./images/tim_kiem_thong_thuong.jpg" width="250px"><br>
      <em>Tìm kiếm thông thường</em>
    </td>
    <td align="center">
      <img src="./images/tim_kiem_bang_ai.jpg" width="250px"><br>
      <em>Tìm kiếm bằng AI</em>
    </td>
    <td align="center">
      <img src="./images/lich_su_tim_kiem.jpg" width="250px"><br>
      <em>Lịch sử tìm kiếm</em>
    </td>
  </tr>
</table>

---

### 7. Tương tác cộng đồng (thích, bình luận, thông báo)

<table>
  <tr>
    <td align="center">
      <img src="./images/tuong_tac_cong_dong.jpg" width="250px"><br>
      <em>Danh sách bài đăng</em>
    </td>
    <td align="center">
      <img src="./images/cmt_replycmt_like.jpg" width="250px"><br>
      <em>Bình luận, trả lời, thích</em>
    </td>
    <td align="center">
      <img src="./images/thong_bao.jpg" width="250px"><br>
      <em>Thông báo tương tác</em>
    </td>
  </tr>
</table>

---

### 8. Quản lý thông tin chung

<table>
  <tr>
    <td align="center">
      <img src="./images/dashboard_admin.jpg" width="250px"><br>
      <em>Dashboard Admin</em>
    </td>
    <td align="center">
      <img src="./images/quan_ly_nguoi_dung_admin.jpg" width="250px"><br>
      <em>Quản lý người dùng</em>
    </td>
    <td align="center">
      <img src="./images/quan_ly_bai_dang_admin.jpg" width="250px"><br>
      <em>Quản lý bài đăng</em>
    </td>
  </tr>
</table>