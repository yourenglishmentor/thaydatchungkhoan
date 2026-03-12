# Danh sách các trang
pages = ["Home", "Trading Portfolio", "Investing Portfolio", "Watchlist", "Financial Freedom Calculator", "Position Sizing Calculator", "Chatbot"]

# Định nghĩa các style cho thanh navbar
styles = {
    "nav": {
        "background-color": "rgb(169, 169, 169)",  # Màu nền đen
    },
    "div": {
        "max-width": "60rem",  # Độ rộng tối đa của phần div
    },
    "span": {
        "border-radius": "0.5rem",  # Đường viền cong
        "color": "rgb(0,0,0)",  # Màu chữ 
        "margin": "0 0.125rem",  # Khoảng cách giữa các thành phần
        "padding": "0.4375rem 0.625rem",  # Khoảng cách nội dung trong span
    },
    "active": {
        "background-color": "rgba(0, 0, 0, 0.2)",  # Màu nền đen với độ mờ khi active
    },
    "hover": {
        "background-color": "rgba(0, 0, 0, 0.3)",  # Màu nền đen với độ mờ khi hover
    },
}
# HTML for the marquee
marquee_html = """
<div style="overflow:hidden; white-space:nowrap;">
  <div style="display:inline-block; padding-left:100%; animation: marquee 50s linear infinite;">
    <p style="font-size:20px;font-weight:bold">Website được xây dựng dưới sự bảo trợ của Khoa TCNH thuộc Đại học Ngoại Thương Hà Nội và sự hỗ trợ từ Khoa CN&KHDL</p>
  </div>
</div>
<style>
@keyframes marquee {
  0% { transform: translate(0, 0); }
  100% { transform: translate(-100%, 0); }
}
</style>
"""