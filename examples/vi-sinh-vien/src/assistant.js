const EXPENSE_RULES = [
  { category: "Ăn uống", words: ["an uong", "an trua", "an sang", "an toi", "com", "bun", "pho", "banh mi", "ca phe", "cafe", "tra sua", "do an", "grabfood", "shopeefood", "food", "lunch", "dinner"] },
  { category: "Đi lại", words: ["di lai", "xang", "xe buyt", "ve xe", "gui xe", "grab", "be bike", "taxi", "di chuyen", "xe om", "bus"] },
  { category: "Học tập", words: ["hoc tap", "hoc phi", "giao trinh", "sach", "tai lieu", "in bai", "photocopy", "but", "vo ghi", "khoa hoc", "course"] },
  { category: "Nhà ở", words: ["tien tro", "tien nha", "thue nha", "tien phong", "ky tuc xa", "nha o", "tien dien", "tien nuoc", "internet", "wifi"] },
  { category: "Mua sắm", words: ["mua sam", "quan ao", "giay dep", "my pham", "shopee", "lazada", "tiki", "phu kien", "shopping"] },
  { category: "Giải trí", words: ["giai tri", "xem phim", "rap phim", "netflix", "spotify", "karaoke", "choi game", "du lich", "concert", "ve show"] },
  { category: "Sức khỏe", words: ["suc khoe", "nha thuoc", "thuoc", "kham benh", "benh vien", "bac si", "gym", "y te"] },
  { category: "Hóa đơn", words: ["hoa don", "thanh toan dien", "thanh toan nuoc", "cuoc dien thoai", "cuoc internet", "dien thoai"] }
];

const INCOME_RULES = [
  { category: "Tiền gia đình", words: ["gia dinh", "bo me", "ba me", "bo gui", "me gui", "tien nha gui"] },
  { category: "Làm thêm", words: ["lam them", "luong", "freelance", "part time", "tien cong", "salary", "ca lam", "tien tip"] },
  { category: "Học bổng", words: ["hoc bong", "scholarship", "thuong hoc tap"] },
  { category: "Trợ cấp", words: ["tro cap", "ho tro", "phu cap", "stipend"] },
  { category: "Bán hàng", words: ["ban hang", "doanh thu", "don hang", "ban do", "thu tien hang"] }
];

function normalizeText(value) {
  return String(value || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLocaleLowerCase("vi-VN")
    .replace(/đ/g, "d");
}

export function suggestCategory(description, type = "expense") {
  const text = normalizeText(description).trim();
  if (!text) return null;
  const rules = type === "income" ? INCOME_RULES : EXPENSE_RULES;
  const match = rules.find(rule => rule.words.some(word => text.includes(normalizeText(word))));
  return match ? match.category : null;
}

function parseDate(value) {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(value || ""));
  if (!match) return null;
  const date = new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3]));
  if (date.getFullYear() !== Number(match[1]) || date.getMonth() + 1 !== Number(match[2]) || date.getDate() !== Number(match[3])) return null;
  date.setHours(0, 0, 0, 0);
  return date;
}

function keyDate(date) {
  return date.getFullYear() + "-" + String(date.getMonth() + 1).padStart(2, "0") + "-" + String(date.getDate()).padStart(2, "0");
}

function dateLabel(date) {
  return new Intl.DateTimeFormat("vi-VN", { day: "2-digit", month: "2-digit", year: "numeric" }).format(date);
}

function monthLabel(date) {
  return "tháng " + String(date.getMonth() + 1).padStart(2, "0") + "/" + date.getFullYear();
}

function shiftDate(date, period, amount) {
  const moved = new Date(date);
  if (period === "day") moved.setDate(moved.getDate() + amount);
  else if (period === "month") moved.setMonth(moved.getMonth() + amount, 1);
  else moved.setFullYear(moved.getFullYear() + amount, 0, 1);
  return moved;
}

function makeRange(period, anchor) {
  const start = new Date(anchor);
  let end;
  if (period === "day") {
    start.setHours(0, 0, 0, 0);
    end = shiftDate(start, "day", 1);
  } else if (period === "year") {
    start.setMonth(0, 1);
    end = new Date(start.getFullYear() + 1, 0, 1);
  } else {
    start.setDate(1);
    end = new Date(start.getFullYear(), start.getMonth() + 1, 1);
  }
  return { start: keyDate(start), end: keyDate(end), startDate: start, endDate: end };
}

function periodTitle(period, anchor) {
  if (period === "day") return "ngày " + dateLabel(anchor);
  if (period === "year") return "năm " + anchor.getFullYear();
  return monthLabel(anchor);
}

function selectPeriod(transactions, range) {
  return transactions.filter(item => {
    const date = String(item.date || "");
    return /^\d{4}-\d{2}-\d{2}$/.test(date) && date >= range.start && date < range.end;
  });
}

function sumType(items, type) {
  return items.reduce((total, item) => total + (item.type === type ? Math.max(0, Number(item.amount) || 0) : 0), 0);
}

function groupExpenses(items) {
  const grouped = new Map();
  items.filter(item => item.type === "expense").forEach(item => {
    const name = String(item.category || "Khác");
    grouped.set(name, (grouped.get(name) || 0) + Math.max(0, Number(item.amount) || 0));
  });
  return Array.from(grouped, ([category, amount]) => ({ category, amount })).sort((a, b) => b.amount - a.amount);
}

function findRecurringExpense(transactions) {
  const groups = new Map();
  transactions.filter(item => item.type === "expense" && item.name && item.date).forEach(item => {
    const name = normalizeText(item.name).replace(/[^a-z0-9 ]/g, " ").replace(/\s+/g, " ").trim();
    if (name.length < 3) return;
    const key = name + "|" + String(item.category || "");
    if (!groups.has(key)) groups.set(key, { name: item.name, category: item.category || "Khác", dates: new Set(), amounts: [] });
    const group = groups.get(key);
    group.dates.add(String(item.date).slice(0, 7));
    group.amounts.push(Number(item.amount) || 0);
  });
  return Array.from(groups.values())
    .filter(group => group.dates.size >= 2)
    .map(group => ({
      name: group.name,
      category: group.category,
      months: group.dates.size,
      average: Math.round(group.amounts.reduce((a, b) => a + b, 0) / group.amounts.length)
    }))
    .sort((a, b) => b.months - a.months || b.average - a.average)
    .slice(0, 3);
}

function percentageChange(current, previous) {
  if (previous <= 0) return null;
  return Math.round((current - previous) / previous * 100);
}

function budgetForPeriod(budgets, period, anchor) {
  if (period === "day") {
    const month = keyDate(new Date(anchor.getFullYear(), anchor.getMonth(), 1)).slice(0, 7);
    return Number(budgets[month]) > 0 ? Number(budgets[month]) : 0;
  }
  if (period === "month") {
    const key = keyDate(new Date(anchor.getFullYear(), anchor.getMonth(), 1)).slice(0, 7);
    return Number(budgets[key]) > 0 ? Number(budgets[key]) : 0;
  }
  const prefix = String(anchor.getFullYear()) + "-";
  return Object.entries(budgets || {}).reduce((sum, entry) => entry[0].startsWith(prefix) && Number(entry[1]) > 0 ? sum + Number(entry[1]) : sum, 0);
}

export function analyzeSpending(transactions = [], budgets = {}, options = {}) {
  const period = ["day", "month", "year"].includes(options.period) ? options.period : "month";
  const anchor = parseDate(options.anchorDate) || new Date();
  const range = makeRange(period, anchor);
  const previousRange = makeRange(period, shiftDate(range.startDate, period, -1));
  const current = selectPeriod(transactions, range);
  const previous = selectPeriod(transactions, previousRange);
  const income = sumType(current, "income");
  const expense = sumType(current, "expense");
  const previousExpense = sumType(previous, "expense");
  const balance = income - expense;
  const rate = income > 0 ? Math.round((balance / income) * 100) : null;
  const categoryTotals = groupExpenses(current);
  const budget = budgetForPeriod(budgets || {}, period, anchor);
  const title = periodTitle(period, anchor);
  const insights = [];
  const recommendations = [];

  if (current.length === 0) {
    insights.push("Chưa có giao dịch nào trong " + title + ". Hãy nhập các khoản thu và chi để bản phân tích có dữ liệu.");
  } else {
    if (income > 0 && balance < 0) {
      insights.push("Chi tiêu đang cao hơn thu nhập " + new Intl.NumberFormat("vi-VN").format(Math.abs(balance)) + " đồng trong kỳ này.");
      recommendations.push("Ưu tiên chi phí thiết yếu, tạm hoãn khoản mua sắm không bắt buộc và kiểm tra các khoản chi lớn.");
    }
    const change = percentageChange(expense, previousExpense);
    if (change !== null && change >= 15) {
      insights.push("Chi tiêu tăng " + change + "% so với kỳ liền trước.");
      recommendations.push("So sánh các giao dịch mới phát sinh với kỳ trước; xem lại danh mục tăng mạnh trước khi chi thêm.");
    } else if (change !== null && change <= -15) {
      insights.push("Chi tiêu giảm " + Math.abs(change) + "% so với kỳ liền trước.");
      recommendations.push("Duy trì các thói quen giúp giảm chi tiêu và chuyển phần tiền dư vào khoản tiết kiệm.");
    } else if (previous.length > 0 && change !== null) {
      insights.push("Mức chi tiêu gần tương đương kỳ liền trước (" + (change > 0 ? "tăng " : change < 0 ? "giảm " : "không đổi ") + Math.abs(change) + "%).");
    }
    if (categoryTotals.length > 0 && expense > 0) {
      const top = categoryTotals[0];
      const share = Math.round(top.amount / expense * 100);
      if (share >= 35) {
        insights.push("Danh mục " + top.category + " chiếm " + share + "% tổng chi tiêu của kỳ.");
        recommendations.push("Đặt giới hạn riêng cho " + top.category + " và xem lại các giao dịch không cần thiết trong nhóm này.");
      }
    }
    if (rate !== null && rate >= 20) {
      insights.push("Bạn đang giữ lại khoảng " + rate + "% thu nhập trong kỳ.");
    } else if (income > 0 && rate !== null && rate < 10) {
      insights.push("Tỷ lệ tiền còn lại chỉ khoảng " + Math.max(0, rate) + "% thu nhập; biên dự phòng khá thấp.");
      recommendations.push("Thử dành một khoản tiết kiệm cố định ngay khi nhận thu nhập, rồi lập giới hạn cho các khoản tùy ý.");
    }
  }

  if (budget > 0) {
    if (period === "day") {
      const month = anchor.getFullYear() + "-" + String(anchor.getMonth() + 1).padStart(2, "0");
      const monthRange = makeRange("month", anchor);
      const monthExpense = sumType(selectPeriod(transactions, monthRange), "expense");
      const daysInMonth = new Date(anchor.getFullYear(), anchor.getMonth() + 1, 0).getDate();
      const dailyGuide = budget / daysInMonth;
      const dayExpense = expense;
      insights.push("Ngân sách " + month + " là " + new Intl.NumberFormat("vi-VN").format(budget) + " đồng, tương đương khoảng " + new Intl.NumberFormat("vi-VN", { maximumFractionDigits: 0 }).format(dailyGuide) + " đồng/ngày.");
      if (dayExpense > dailyGuide) recommendations.push("Khoản chi trong ngày cao hơn mức bình quân ngân sách khoảng " + new Intl.NumberFormat("vi-VN").format(Math.round(dayExpense - dailyGuide)) + " đồng. Cân đối lại các ngày còn lại trong tháng.");
      else recommendations.push("Chi tiêu ngày này nằm trong mức bình quân ngân sách. Tiếp tục theo dõi tổng chi tháng, hiện ở mức " + new Intl.NumberFormat("vi-VN").format(monthExpense) + " đồng.");
    } else if (period === "month") {
      const remaining = budget - expense;
      const lastDay = new Date(anchor.getFullYear(), anchor.getMonth() + 1, 0).getDate();
      const daysLeft = Math.max(1, lastDay - anchor.getDate() + 1);
      if (remaining < 0) {
        insights.push("Bạn đã vượt ngân sách kỳ này " + new Intl.NumberFormat("vi-VN").format(Math.abs(remaining)) + " đồng.");
        recommendations.push("Dừng hoặc giảm các khoản tùy ý; kiểm tra các khoản chi định kỳ trước khi đặt mục tiêu mới.");
      } else {
        insights.push("Đã dùng " + Math.round(expense / budget * 100) + "% ngân sách; còn " + new Intl.NumberFormat("vi-VN").format(remaining) + " đồng.");
        recommendations.push("Từ ngày mốc đã chọn đến cuối tháng, mức trần tham khảo là khoảng " + new Intl.NumberFormat("vi-VN", { maximumFractionDigits: 0 }).format(remaining / daysLeft) + " đồng/ngày.");
      }
    } else {
      const remaining = budget - expense;
      const monthKeysLeft = Math.max(1, 12 - anchor.getMonth());
      if (remaining < 0) {
        insights.push("Tổng chi đã vượt tổng ngân sách năm được khai báo " + new Intl.NumberFormat("vi-VN").format(Math.abs(remaining)) + " đồng.");
        recommendations.push("Rà soát các tháng vượt kế hoạch và đặt lại giới hạn cho những tháng tiếp theo.");
      } else {
        insights.push("Tổng ngân sách năm đã khai báo là " + new Intl.NumberFormat("vi-VN").format(budget) + " đồng; kỳ đang xem còn " + new Intl.NumberFormat("vi-VN").format(remaining) + " đồng.");
        recommendations.push("Mức trần tham khảo cho mỗi tháng còn lại trong năm là khoảng " + new Intl.NumberFormat("vi-VN", { maximumFractionDigits: 0 }).format(remaining / monthKeysLeft) + " đồng.");
      }
    }
  } else {
    recommendations.push(period === "day" ? "Đặt ngân sách tháng để có mức chi tham khảo theo ngày." : period === "month" ? "Đặt ngân sách tháng để nhận cảnh báo khi gần hoặc vượt giới hạn." : "Đặt ngân sách theo các tháng để ước lượng kế hoạch tài chính cả năm.");
  }

  const recurring = findRecurringExpense(transactions);
  if (recurring.length) {
    const first = recurring[0];
    insights.push("Phát hiện " + recurring.length + " khoản chi có tên và danh mục lặp lại ở nhiều tháng; cần kiểm tra xem có phải khoản định kỳ không.");
    recommendations.push("Kiểm tra khoản lặp “" + first.name + "” (trung bình " + new Intl.NumberFormat("vi-VN").format(first.average) + " đồng/lần) và lập nhắc lịch nếu đây là hóa đơn hoặc khoản cố định.");
  }

  if (recommendations.length === 0) {
    recommendations.push("Tiếp tục ghi lại giao dịch thường xuyên; gợi ý sẽ cụ thể hơn khi có thêm dữ liệu qua nhiều kỳ.");
  }

  return {
    period,
    title,
    start: range.start,
    end: range.end,
    transactions: current.length,
    income,
    expense,
    balance,
    savingRate: rate,
    budget,
    insights: insights.slice(0, 5),
    recommendations: recommendations.slice(0, 4)
  };
}
