import React from "react";
import Banner from "../components/Banner";
// import CategoryList from "../components/CategoryList";
import VoucherList from "../components/Voucherlist";
import SearchBar from "../components/SearchBar";
import "../styles/home.css";
import { Link } from "react-router-dom";


// anh
import freeshipImg from "../img/TH/Freeship.jpg";
import Laza from "../img/TH/laza.png";
import Noihinh from "../img/TH/noihinh.png";
import Shope from "../img/TH/shopee.png";
import Tramj from "../img/TH/Tramj.jpg";
import shopee1 from "../img/TH/shopee1.png";

// anh tin tức 
import img0 from "../img/Tin_tuc/sale5.webp";
import img1 from "../img/Tin_tuc/1.webp";
import img2 from "../img/Tin_tuc/2.webp";
import img3 from "../img/Tin_tuc/3.webp";
import img4 from "../img/Tin_tuc/4.webp";
import img5 from "../img/Tin_tuc/5.webp";
import img6 from "../img/Tin_tuc/6.webp";
import img7 from "../img/Tin_tuc/7.webp";
import img8 from "../img/Tin_tuc/8.webp";
import img9 from "../img/Tin_tuc/9.webp";

function Home(props) {

  return (
    <div className="home-page">
      <Banner />
      <div className="carousel">
        <div className="carousel-images">
          <img src={freeshipImg} alt="Banner 1" />
          <img src={Laza} alt="Banner 1" />
          <img src={Noihinh} alt="Banner 3" />
          <img src={Shope} alt="Banner 3" />
          <img src={Tramj} alt="Banner 3" />
          <img src={shopee1} alt="Banner 3" />
          <img src={freeshipImg} alt="Banner 1" />
          <img src={Noihinh} alt="Banner 3" />
          <img src={Laza} alt="Banner 1" />
          <img src={Tramj} alt="Banner 3" />

        </div>
      </div>
      <div className="search-bar">
        <SearchBar />
      </div>

      {/* <section className="category-section">
        <h2>Danh mục voucher</h2>
        <CategoryList />
      </section> */}

      <section className="featured-section">
        <h2>Voucher nổi bật</h2>
        <VoucherList setToast={props.setToast} />
        <div style={{ textAlign: "center", margin: "24px 0" }}>
          <Link to="/deals">
            <button className="load-more-btn">Xem thêm voucher</button>
          </Link>
        </div>
      </section>


      <section className="news-section">
        <h2>Tin Tức</h2>
        <div className="carousel_tt">
          <div className="carousel-track">
            <div className="news-card">
              <img src={img0} alt="Lazada 5.5 Sale" />
              <div className="content">
                <h3>Lazada 5.5: Giảm 50%, Voucher Max 1 Triệu,</h3>
                <p>
                  Lazada 5.5 - Sale Giảm 50% có gì HOT? Voucher Max 1 triệu, Voucher Chớp Nhoáng giảm 70%, Voucher Gian Hàng giảm đến 20%... Cùng Voux.id.vn tìm hiểu ngay ...
                </p>
              </div>
            </div>
            <div className="news-card">
              <img src={img1} alt="Lazada 5.5 Sale" />
              <div className="content">
                <h3>
                  Mã Shopee Live Xả hàng là gì? Cách săn thế nào?
                </h3>
                <p>
                  Mã Shopee Live Xả hàng là gì? Cách săn loại voucher Shopee Live này như thế nào? Hãy cùng Voux.id.vn tìm hiểu ngay trong bài viết này nhé!...
                </p>
              </div>
            </div>
            <div className="news-card">
              <img src={img2} alt="Lazada 5.5 Sale" />
              <div className="content">
                <h3>Làm sao để xóa/khôi phục video đã xóa trên Shopee</h3>
                <p>
                  Làm sao để xóa/khôi phục video đã xóa trên Shopee Video? Hãy cùng Voux.id.vn tìm hiểu chi tiết cách thực hiện trong bài viết sau đây....
                </p>
              </div>
            </div>
            <div className="news-card">
              <img src={img3} alt="Lazada 5.5 Sale" />
              <div className="content">
                <h3>Làm sao để báo cáo vi phạm trên Shopee Video?</h3>
                <p>
                  Làm thế nào để gửi báo cáo một video vi phạm Tiêu chuẩn cộng đồng trên Shopee Video? Cần làm gì nếu video của bạn bị tài khoản khác sao chép và đăng lên tran...
                </p>
              </div>
            </div>
            <div className="news-card">
              <img src={img4} alt="Lazada 5.5 Sale" />
              <div className="content">
                <h3>Làm sao để xem lại video đã xem trên Shopee Video?</h3>
                <p>
                  Bạn muốn xem lại một video đã xem trên Shopee Video? Bạn muốn xem lại những video đã lưu trên Shopee Video? Cách thực hiện thế nào? Hãy cùng Voux.id.vn t...
                </p>
              </div>
            </div>
            <div className="news-card">
              <img src={img5} alt="Lazada 5.5 Sale" />
              <div className="content">
                <h3>Làm sao để chặn một tài khoản bất kỳ trên Shopee</h3>
                <p>
                  Bạn không muốn bị làm phiền bởi các video, bình luận, tương tác của một tài khoản nào đó trên Shopee Video. Ngay bây giờ cùng Voux.id.vn tìm hiểu cách ch...
                </p>
              </div>
            </div>
            <div className="news-card">
              <img src={img6} alt="Lazada 5.5 Sale" />
              <div className="content">
                <h3>Game Bus Out Lazada chơi ở đâu? Cách chơi ra sao?</h3>
                <p>
                  Game Bus Out Lazada chơi ở đâu? Cách chơi ra sao? Làm sao để kiếm được nhiều phần thưởng từ game này? Cùng Voux.id.vn tìm hiểu câu trả lời trong bài viết...
                </p>
              </div>
            </div>
            <div className="news-card">
              <img src={img7} alt="Lazada 5.5 Sale" />
              <div className="content">
                <h3>Cách săn voucher Youtube Shopee giảm 20% tối đa 2</h3>
                <p>
                  Làm sao để săn được voucher Youtube Shopee giảm 20% tối đa 2 triệu cho đơn từ 500K? Làm sao để không bị lọc mã Youtube Shopping? Làm thế nào để gắn được sản ...
                </p>
              </div>
            </div>
            <div className="news-card">
              <img src={img8} alt="Lazada 5.5 Sale" />
              <div className="content">
                <h3>Hạng thành viên Nô Tì là gì? Có ưu đãi gì HOT?</h3>
                <p>
                  Hạng thành viên Nô Tì là gì? Có ưu đãi gì HOT khi ở hạng cao hơn? Làm sao để thăng hạng nhanh nhất? Cùng Voux.id.vn tìm hiểu ngay trong bài viết này nhé!...
                </p>
              </div>
            </div>
            <div className="news-card">
              <img src={img9} alt="Lazada 5.5 Sale" />
              <div className="content">
                <h3>Cách tìm sản phẩm Shopee trên Youtube để áp mã 25%</h3>
                <p>
                  Shopee vừa ra mắt chương trình chương trình hấp dẫn "Mua hàng trên YouTube - giảm giá 25%". Vậy làm thế nào để tìm sản phẩm Shopee trên Youtube? Cùng Bloggia...
                </p>
              </div>
            </div>


          </div>
        </div>
      </section>

      <section className="faq-section">
        <h2>Câu Hỏi Thường Gặp</h2>
        <div className="faq-grid">
          <div className="faq-item">Lỗi M01 Shopee là gì? Cách khắc phục hiệu quả</div>
          <div className="faq-item">Shopee có bán những gói bảo hiểm nào?</div>
          <div className="faq-item">Kho Xuyen A SOC Shopee ở đâu? Sau bao lâu thì nhận được hàng?</div>
          <div className="faq-item">Không thanh toán khoản vay SEasy Vay Tiêu Dùng có sao không?</div>
          <div className="faq-item">Chơi game Quà tặng Shopee ở đâu? Cách chơi ra sao?</div>
          <div className="faq-item">Thử thách Shopee, thử thách Shopee Mall ở đâu? Mở mấy giờ?</div>
          <div className="faq-item">Cách thay đổi số điện thoại Shopee như thế nào?</div>
          <div className="faq-item">Cách săn voucher Youtube Shopee giảm 20% tối đa 2 triệu</div>
        </div>
      </section>


      {/* 
      <div className="chatbot-widget">
        <ChatbotWidget />
      </div> */}
    </div>
  );
}

export default Home;