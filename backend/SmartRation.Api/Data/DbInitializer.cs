using System.Security.Cryptography;
using System.Text;
using Microsoft.EntityFrameworkCore;
using SmartRation.Api.Models;

namespace SmartRation.Api.Data;

// Applies pending migrations and, only if the database is empty, seeds
// reference/demo data so the app is usable immediately after first run.
// Demo accounts intentionally mirror the ones the frontend prototype
// already advertised (rural/shop/officer @example.com, password demo123).
//
// Everything this seeder creates is synthetic (DataSource = SYNTHETIC_DEMO
// on every verification-related row) — no real Aadhaar, passbook or
// beneficiary data exists anywhere in this system.
public static class DbInitializer
{
    // People who can book the same 5-minute collection slot.
    private const int DefaultSlotCapacity = 2;

    // Capacity used by earlier seeds; migrated to DefaultSlotCapacity on startup.
    private const int LegacySlotCapacity = 5;

    private static readonly string[] FirstNames =
    [
        "Ramesh", "Suresh", "Mahesh", "Ganesh", "Rajesh", "Dinesh", "Sanjay", "Vijay", "Ajay", "Prakash",
        "Anil", "Sunil", "Ravi", "Kiran", "Manoj", "Deepak", "Arun", "Ashok", "Vinod", "Pramod",
        "Sunita", "Kavita", "Savita", "Lalita", "Anita", "Sarita", "Rekha", "Meena", "Neha", "Pooja",
        "Priya", "Shobha", "Nirmala", "Kamala", "Vimala", "Shanta", "Geeta", "Seema", "Rita", "Usha"
    ];

    private static readonly string[] LastNames =
    [
        "Patil", "Deshmukh", "More", "Jadhav", "Shinde", "Pawar", "Kale", "Wagh", "Gaikwad", "Bhosale",
        "Chavan", "Kadam", "Sawant", "Thakur", "Gawande", "Meshram", "Wankhede", "Borkar", "Shende", "Ingle"
    ];

    private static readonly (string Name, string Taluka, string Village, double Lat, double Lng)[] ExtraShops =
    [
        ("Hingna Ration Shop", "Hingna", "Hingna", 21.0947, 79.0177),
        ("Kamptee Ration Shop", "Kamptee", "Kamptee", 21.2185, 79.1927),
        ("Wadi Ration Shop", "Nagpur Rural", "Wadi", 21.2016, 78.9814),
        ("Mouda Ration Shop", "Mouda", "Mouda", 21.3799, 79.3524),
        ("Ramtek Ration Shop", "Ramtek", "Ramtek", 21.3959, 79.3306),
        ("Katol Ration Shop", "Katol", "Katol", 21.2667, 78.5833),
        ("Umred Ration Shop", "Umred", "Umred", 20.8500, 79.3333),
        ("Saoner Ration Shop", "Saoner", "Saoner", 21.3833, 78.9167)
    ];

    public static async Task InitializeAsync(SmartRationDbContext db, string qrSecret)
    {
        await db.Database.MigrateAsync();

        if (!await db.RationItems.AnyAsync())
        {
            db.RationItems.AddRange(
                new RationItem { RationType = RationType.Rice, Name = "Rice", VernacularName = "Tandul", Unit = "kg", StandardQuotaPerBooking = 5 },
                new RationItem { RationType = RationType.Wheat, Name = "Wheat", VernacularName = "Gahu", Unit = "kg", StandardQuotaPerBooking = 5 },
                new RationItem { RationType = RationType.Sugar, Name = "Sugar", VernacularName = "Sakhar", Unit = "kg", StandardQuotaPerBooking = 1 },
                new RationItem { RationType = RationType.Pulses, Name = "Pulses", VernacularName = "Daal", Unit = "kg", StandardQuotaPerBooking = 2 },
                new RationItem { RationType = RationType.EdibleOil, Name = "Edible Oil", VernacularName = "Tel", Unit = "L", StandardQuotaPerBooking = 1 },
                new RationItem { RationType = RationType.Salt, Name = "Salt", VernacularName = "Mith", Unit = "kg", StandardQuotaPerBooking = 1 }
            );
            await db.SaveChangesAsync();
        }

        if (!await db.RationShops.AnyAsync())
        {
            db.RationShops.AddRange(
                new RationShop
                {
                    ShopName = "Satnavari Ration Shop",
                    ShopCode = "SR-SATNAVARI-001",
                    Address = "Main Road, Satnavari",
                    District = "Nagpur",
                    State = "Maharashtra",
                    Taluka = "Nagpur Rural",
                    Village = "Satnavari",
                    Latitude = 21.1904,
                    Longitude = 79.0850,
                    IsActive = true
                },
                new RationShop
                {
                    ShopName = "Koradi Ration Shop",
                    ShopCode = "SR-KORADI-001",
                    Address = "Station Road, Koradi",
                    District = "Nagpur",
                    State = "Maharashtra",
                    Taluka = "Kamptee",
                    Village = "Koradi",
                    Latitude = 21.2472,
                    Longitude = 79.1197,
                    IsActive = true
                }
            );
            await db.SaveChangesAsync();
        }

        // Scale up to 10 shops total (minimum required for the map/demo dataset).
        if (await db.RationShops.CountAsync() < 10)
        {
            var index = 1;
            foreach (var s in ExtraShops)
            {
                db.RationShops.Add(new RationShop
                {
                    ShopName = s.Name,
                    ShopCode = $"SHOP-DEMO-{index:D3}",
                    Address = $"Main Road, {s.Village}",
                    District = "Nagpur",
                    State = "Maharashtra",
                    Taluka = s.Taluka,
                    Village = s.Village,
                    Latitude = s.Lat,
                    Longitude = s.Lng,
                    IsActive = true
                });
                index++;
            }
            await db.SaveChangesAsync();
        }

        var satnavariShop = await db.RationShops.FirstAsync(s => s.ShopCode == "SR-SATNAVARI-001");
        var allShops = await db.RationShops.OrderBy(s => s.Id).ToListAsync();

        if (!await db.RationSchemes.AnyAsync())
        {
            var nfsa = new RationScheme
            {
                SchemeCode = "DEMO-NFSA",
                Name = "Demo National Food Security Scheme",
                Description = "Synthetic demo scheme modeled loosely on NFSA-style entitlements. Not a real government scheme.",
                IsActive = true
            };
            var aay = new RationScheme
            {
                SchemeCode = "DEMO-AAY",
                Name = "Demo Priority Household Scheme",
                Description = "Synthetic demo scheme with a higher flat entitlement, modeled loosely on Antyodaya-style schemes. Not a real government scheme.",
                IsActive = true
            };
            db.RationSchemes.AddRange(nfsa, aay);
            await db.SaveChangesAsync();

            db.SchemeEntitlementItems.AddRange(
                new SchemeEntitlementItem { RationSchemeId = nfsa.Id, RationType = RationType.Rice, QuotaPerEligibleMemberPerMonth = 5 },
                new SchemeEntitlementItem { RationSchemeId = nfsa.Id, RationType = RationType.Wheat, QuotaPerEligibleMemberPerMonth = 3 },
                new SchemeEntitlementItem { RationSchemeId = nfsa.Id, RationType = RationType.Sugar, QuotaPerEligibleMemberPerMonth = 1 },
                new SchemeEntitlementItem { RationSchemeId = nfsa.Id, RationType = RationType.Pulses, QuotaPerEligibleMemberPerMonth = 1 },
                new SchemeEntitlementItem { RationSchemeId = nfsa.Id, RationType = RationType.EdibleOil, QuotaPerEligibleMemberPerMonth = 0.5m },
                new SchemeEntitlementItem { RationSchemeId = nfsa.Id, RationType = RationType.Salt, QuotaPerEligibleMemberPerMonth = 0.25m },
                new SchemeEntitlementItem { RationSchemeId = aay.Id, RationType = RationType.Rice, QuotaPerEligibleMemberPerMonth = 7 },
                new SchemeEntitlementItem { RationSchemeId = aay.Id, RationType = RationType.Wheat, QuotaPerEligibleMemberPerMonth = 4 },
                new SchemeEntitlementItem { RationSchemeId = aay.Id, RationType = RationType.Sugar, QuotaPerEligibleMemberPerMonth = 1.5m },
                new SchemeEntitlementItem { RationSchemeId = aay.Id, RationType = RationType.Pulses, QuotaPerEligibleMemberPerMonth = 1.5m },
                new SchemeEntitlementItem { RationSchemeId = aay.Id, RationType = RationType.EdibleOil, QuotaPerEligibleMemberPerMonth = 1 },
                new SchemeEntitlementItem { RationSchemeId = aay.Id, RationType = RationType.Salt, QuotaPerEligibleMemberPerMonth = 0.5m }
            );
            await db.SaveChangesAsync();
        }

        if (!await db.Users.AnyAsync())
        {
            db.Users.AddRange(
                new User
                {
                    FullName = "Rahul Patil",
                    Email = "rural@example.com",
                    MobileNumber = "9876543210",
                    PasswordHash = BCrypt.Net.BCrypt.HashPassword("demo123"),
                    Role = UserRole.RuralUser,
                    IsActive = true
                },
                new User
                {
                    FullName = "Satnavari Shop Owner",
                    Email = "shop@example.com",
                    MobileNumber = "9876543211",
                    PasswordHash = BCrypt.Net.BCrypt.HashPassword("demo123"),
                    Role = UserRole.ShopOwner,
                    RationShopId = satnavariShop.Id,
                    IsActive = true
                },
                new User
                {
                    FullName = "District Government Officer",
                    Email = "officer@example.com",
                    MobileNumber = "9876543212",
                    PasswordHash = BCrypt.Net.BCrypt.HashPassword("demo123"),
                    Role = UserRole.GovernmentOfficial,
                    IsActive = true
                }
            );
            await db.SaveChangesAsync();
        }

        if (!await db.Inventory.AnyAsync())
        {
            for (var i = 0; i < allShops.Count; i++)
            {
                var shop = allShops[i];
                // Rotate through Critical / Low / Normal stock tiers so the map and
                // shop dashboards have realistic variety to display out of the box.
                var tier = i % 4;

                decimal Scale(decimal min) => tier switch
                {
                    0 => Math.Round(min * 0.3m, 0), // Critical
                    1 => Math.Round(min * 0.8m, 0), // Low
                    _ => Math.Round(min * (3.0m + i * 0.15m), 0) // Normal, comfortably stocked
                };

                db.Inventory.AddRange(
                    new Inventory { RationShopId = shop.Id, RationType = RationType.Rice, AvailableQuantity = Scale(300), AllocatedQuantity = 0, MinimumStockLevel = 300 },
                    new Inventory { RationShopId = shop.Id, RationType = RationType.Wheat, AvailableQuantity = Scale(300), AllocatedQuantity = 0, MinimumStockLevel = 300 },
                    new Inventory { RationShopId = shop.Id, RationType = RationType.Sugar, AvailableQuantity = Scale(200), AllocatedQuantity = 0, MinimumStockLevel = 200 },
                    new Inventory { RationShopId = shop.Id, RationType = RationType.Pulses, AvailableQuantity = Scale(150), AllocatedQuantity = 0, MinimumStockLevel = 150 },
                    new Inventory { RationShopId = shop.Id, RationType = RationType.EdibleOil, AvailableQuantity = Scale(100), AllocatedQuantity = 0, MinimumStockLevel = 100 },
                    new Inventory { RationShopId = shop.Id, RationType = RationType.Salt, AvailableQuantity = Scale(80), AllocatedQuantity = 0, MinimumStockLevel = 80 }
                );
            }
            await db.SaveChangesAsync();
        }

        // Databases seeded before the per-slot capacity became 2 still hold the
        // old default of 5. Bring them in line, but never below what's already
        // booked in a slot.
        await db.TimeSlots
            .Where(s => s.Capacity == LegacySlotCapacity)
            .ExecuteUpdateAsync(u => u.SetProperty(
                s => s.Capacity,
                s => s.BookedCount > DefaultSlotCapacity ? s.BookedCount : DefaultSlotCapacity));

        if (!await db.TimeSlots.AnyAsync())
        {
            var today = DateTime.UtcNow.Date;

            // -5..+2: past days give completed collections something to attach to
            // (so entitlement "already collected this month" isn't always zero),
            // today/+1/+2 give live slots to book and test against.
            foreach (var shop in allShops)
            {
                for (var dayOffset = -5; dayOffset <= 2; dayOffset++)
                {
                    var slotDate = today.AddDays(dayOffset);
                    for (var minutes = 9 * 60; minutes < 17 * 60; minutes += 5)
                    {
                        db.TimeSlots.Add(new TimeSlot
                        {
                            RationShopId = shop.Id,
                            SlotDate = slotDate,
                            StartTime = TimeSpan.FromMinutes(minutes),
                            EndTime = TimeSpan.FromMinutes(minutes + 5),
                            Capacity = DefaultSlotCapacity,
                            BookedCount = 0
                        });
                    }
                }
            }

            await db.SaveChangesAsync();
        }

        // Everything below (beneficiaries, families, bookings, collections) is
        // guarded by a single check so it only ever runs once.
        if (await db.Beneficiaries.AnyAsync())
        {
            return;
        }

        var schemes = await db.RationSchemes.OrderBy(s => s.Id).ToListAsync();
        var nfsaScheme = schemes.First(s => s.SchemeCode == "DEMO-NFSA");
        var aayScheme = schemes.First(s => s.SchemeCode == "DEMO-AAY");

        var rahul = await db.Users.FirstAsync(u => u.Email == "rural@example.com");
        var beneficiaries = new List<Beneficiary>();

        // Beneficiary #1 is the existing demo login; #2..#50 are generated.
        for (var i = 1; i <= 50; i++)
        {
            User user;
            if (i == 1)
            {
                user = rahul;
            }
            else
            {
                var fullName = $"{FirstNames[i % FirstNames.Length]} {LastNames[i % LastNames.Length]}";
                user = new User
                {
                    FullName = fullName,
                    Email = $"beneficiary{i}@example.com",
                    MobileNumber = $"90{i:D8}",
                    PasswordHash = BCrypt.Net.BCrypt.HashPassword("demo123"),
                    Role = UserRole.RuralUser,
                    IsActive = i != 49 // one deliberately inactive account for test coverage
                };
                db.Users.Add(user);
                await db.SaveChangesAsync();
            }

            var shop = allShops[(i - 1) % allShops.Count];
            var scheme = i % 5 == 0 ? aayScheme : nfsaScheme;
            var village = shop.Village ?? shop.District;
            var headAge = 28 + (i % 20);

            var family = new Family
            {
                FamilyCode = string.Empty,
                RationShopId = shop.Id,
                RationSchemeId = scheme.Id,
                DataSource = "SYNTHETIC_DEMO"
            };
            db.Families.Add(family);
            await db.SaveChangesAsync();
            family.FamilyCode = $"FAM-DEMO-{family.Id:D4}";

            var memberCount = 1 + (i % 5); // 1..5 additional members beyond the head
            db.FamilyMembers.Add(new FamilyMember
            {
                FamilyId = family.Id,
                FullName = user.FullName,
                Age = headAge,
                Relationship = FamilyRelationship.Head,
                Eligibility = EligibilityStatus.Eligible,
                DataSource = "SYNTHETIC_DEMO"
            });

            var relationships = new[] { FamilyRelationship.Spouse, FamilyRelationship.Son, FamilyRelationship.Daughter, FamilyRelationship.Parent, FamilyRelationship.Other };
            for (var m = 0; m < memberCount; m++)
            {
                var eligibility = (i + m) % 11 == 0
                    ? EligibilityStatus.NotEligible
                    : (i + m) % 13 == 0
                        ? EligibilityStatus.Pending
                        : (i + m) % 17 == 0
                            ? EligibilityStatus.VerificationRequired
                            : EligibilityStatus.Eligible;

                db.FamilyMembers.Add(new FamilyMember
                {
                    FamilyId = family.Id,
                    FullName = $"{FirstNames[(i + m + 7) % FirstNames.Length]} {LastNames[i % LastNames.Length]}",
                    Age = relationships[m % relationships.Length] switch
                    {
                        FamilyRelationship.Son or FamilyRelationship.Daughter => 3 + (m * 4 % 17),
                        FamilyRelationship.Parent => 55 + (m % 15),
                        _ => 25 + (m % 20)
                    },
                    Relationship = relationships[m % relationships.Length],
                    Eligibility = eligibility,
                    DataSource = "SYNTHETIC_DEMO"
                });
            }
            await db.SaveChangesAsync();

            var beneficiary = new Beneficiary
            {
                BeneficiaryCode = string.Empty,
                Address = village,
                Gender = i % 29 == 0 ? Gender.Other : i % 2 == 0 ? Gender.Female : Gender.Male,
                DateOfBirth = DateTime.UtcNow.AddYears(-headAge).AddDays(i * 3 % 365),
                Village = village,
                District = shop.District,
                State = shop.State,
                Pincode = $"4410{i % 90:D2}",
                UserId = user.Id,
                FamilyId = family.Id,
                IsActive = true,
                IsBlocked = i % 23 == 0, // rare blocked case for test coverage
                DataSource = "SYNTHETIC_DEMO"
            };
            db.Beneficiaries.Add(beneficiary);
            await db.SaveChangesAsync();
            beneficiary.BeneficiaryCode = $"BEN-DEMO-{beneficiary.Id:D4}";

            // Deliberately uses moduli coprime with the shop round-robin (%10) so
            // verification-status variety doesn't correlate with shop assignment.
            var aadhaarStatus = i % 9 == 0
                ? AadhaarVerificationStatus.Failed
                : i % 13 == 0
                    ? AadhaarVerificationStatus.Expired
                    : i % 7 == 2
                        ? AadhaarVerificationStatus.Pending
                        : AadhaarVerificationStatus.Verified;

            db.AadhaarVerifications.Add(new AadhaarVerification
            {
                BeneficiaryId = beneficiary.Id,
                AadhaarReferenceId = $"AAD-DEMO-{beneficiary.Id:D6}",
                AadhaarMasked = $"XXXX-XXXX-{((beneficiary.Id * 6173) % 9000 + 1000)}",
                Status = aadhaarStatus,
                VerificationDate = aadhaarStatus is AadhaarVerificationStatus.Verified or AadhaarVerificationStatus.Expired ? DateTime.UtcNow.AddMonths(-1) : null,
                VerificationSource = "SYNTHETIC_DEMO",
                VerificationMode = "PRE_VERIFIED"
            });

            var passbookStatus = i % 11 == 0
                ? PassbookVerificationStatus.Pending
                : i % 17 == 0
                    ? PassbookVerificationStatus.Failed
                    : PassbookVerificationStatus.Verified;

            db.PassbookVerifications.Add(new PassbookVerification
            {
                BeneficiaryId = beneficiary.Id,
                PassbookNumber = $"PB-DEMO-{beneficiary.Id:D4}",
                Status = "ACTIVE",
                VerificationStatus = passbookStatus,
                LastUpdated = DateTime.UtcNow.AddDays(-(i % 20)),
                VerificationSource = "SYNTHETIC_DEMO"
            });

            var mobileStatus = i % 15 == 0 ? MobileVerificationStatus.NotVerified : MobileVerificationStatus.Verified;
            db.MobileVerifications.Add(new MobileVerification
            {
                BeneficiaryId = beneficiary.Id,
                MobileMasked = $"{new string('*', 6)}{user.MobileNumber[^4..]}",
                Status = mobileStatus,
                VerifiedAt = mobileStatus == MobileVerificationStatus.Verified ? DateTime.UtcNow.AddMonths(-1) : null,
                VerificationSource = "SYNTHETIC_DEMO"
            });

            beneficiaries.Add(beneficiary);
        }

        await db.SaveChangesAsync();

        // ---- Bookings + tokens (100+) spread across past/today/future, with a
        // mix of statuses so QR verification has valid/used/cancelled cases to
        // demonstrate against. ----
        var todayDate = DateTime.UtcNow.Date;

        foreach (var beneficiary in beneficiaries)
        {
            var bookingsForThisBeneficiary = 2 + (beneficiary.Id % 2); // 2 or 3 each -> 100+ total
            var shopId = await db.Families.Where(f => f.Id == beneficiary.FamilyId).Select(f => f.RationShopId).FirstAsync();

            for (var b = 0; b < bookingsForThisBeneficiary; b++)
            {
                var dayOffset = ((beneficiary.Id + b) % 8) - 5; // -5..+2
                var slotDate = todayDate.AddDays(dayOffset);

                // SQLite can't ORDER BY a TimeSpan column server-side — materialize then sort client-side.
                var availableSlots = await db.TimeSlots
                    .Where(s => s.RationShopId == shopId && s.SlotDate == slotDate && s.BookedCount < s.Capacity)
                    .ToListAsync();

                var candidateSlot = availableSlots
                    .OrderBy(s => s.StartTime)
                    .Skip((beneficiary.Id + b) % 20)
                    .FirstOrDefault() ?? availableSlots.FirstOrDefault();

                if (candidateSlot is null)
                {
                    continue;
                }

                candidateSlot.BookedCount += 1;

                TokenStatus status;
                if (dayOffset < 0)
                {
                    status = (beneficiary.Id + b) % 6 == 0 ? TokenStatus.Cancelled : TokenStatus.Confirmed;
                }
                else
                {
                    status = TokenStatus.Confirmed;
                }

                var token = new Token
                {
                    TokenNumber = string.Empty,
                    UserId = beneficiary.UserId,
                    RationShopId = shopId,
                    TimeSlotId = candidateSlot.Id,
                    Status = status,
                    CreatedAt = DateTime.UtcNow.AddDays(dayOffset - 1)
                };
                db.Tokens.Add(token);
                await db.SaveChangesAsync();

                token.TokenNumber = $"SR-{token.CreatedAt:yyyy}-{token.Id:D6}";
                token.QRCodeValue = ComputeQrValue(qrSecret, token.Id, token.TokenNumber);

                var items = new List<TokenItem>
                {
                    new() { TokenId = token.Id, RationType = RationType.Rice, Quantity = 5 },
                    new() { TokenId = token.Id, RationType = RationType.Wheat, Quantity = 3 }
                };
                if ((beneficiary.Id + b) % 2 == 0)
                {
                    items.Add(new TokenItem { TokenId = token.Id, RationType = RationType.Sugar, Quantity = 1 });
                }
                db.TokenItems.AddRange(items);
                await db.SaveChangesAsync();

                // Past, non-cancelled bookings: mark most as collected so
                // entitlement history and previous-collections have real data.
                if (dayOffset < 0 && status == TokenStatus.Confirmed && (beneficiary.Id + b) % 4 != 0)
                {
                    token.Status = TokenStatus.Completed;
                    token.CollectedAt = slotDate.AddHours(10);

                    var collection = new RationCollection
                    {
                        CollectionCode = string.Empty,
                        TokenId = token.Id,
                        BeneficiaryId = beneficiary.Id,
                        RationShopId = shopId,
                        OperatorUserId = rahul.Id, // synthetic seed data — not a real operator action
                        VerificationMethod = "QR",
                        CollectedAt = token.CollectedAt.Value,
                        Items = items.Select(i => new RationCollectionItem { RationType = i.RationType, Quantity = i.Quantity }).ToList()
                    };
                    db.RationCollections.Add(collection);
                    await db.SaveChangesAsync();
                    collection.CollectionCode = $"COL-DEMO-{collection.Id:D6}";
                    await db.SaveChangesAsync();
                }
                else
                {
                    await db.SaveChangesAsync();
                }
            }
        }

        // ---- /qr-demo showcase tokens — fixed, human-readable QR aliases so
        // they can be printed/displayed and physically scanned with a camera.
        // SRQR-INVALID-999 is deliberately NOT seeded here: it has no matching
        // token, so QrService naturally rejects it as "not recognized". ----
        await SeedDemoQrShowcaseAsync(db, rahul, satnavariShop.Id, todayDate);
    }

    private static async Task SeedDemoQrShowcaseAsync(SmartRationDbContext db, User rahul, int shopId, DateTime todayDate)
    {
        var slots = await db.TimeSlots
            .Where(s => s.RationShopId == shopId && s.BookedCount < s.Capacity)
            .ToListAsync();

        TimeSlot? PickSlot(DateTime date) => slots.FirstOrDefault(s => s.SlotDate == date && s.BookedCount < s.Capacity);

        async Task<Token> CreateShowcaseTokenAsync(string qrAlias, DateTime slotDate, TokenStatus status, DateTime? collectedAt)
        {
            var slot = PickSlot(slotDate) ?? slots.First(s => s.BookedCount < s.Capacity);
            slot.BookedCount += 1;

            var token = new Token
            {
                TokenNumber = string.Empty,
                UserId = rahul.Id,
                RationShopId = shopId,
                TimeSlotId = slot.Id,
                Status = status,
                CreatedAt = DateTime.UtcNow,
                CollectedAt = collectedAt
            };
            db.Tokens.Add(token);
            await db.SaveChangesAsync();

            token.TokenNumber = $"SR-DEMO-{token.Id:D6}";
            token.QRCodeValue = qrAlias;
            db.TokenItems.Add(new TokenItem { TokenId = token.Id, RationType = RationType.Rice, Quantity = 5 });
            db.TokenItems.Add(new TokenItem { TokenId = token.Id, RationType = RationType.Wheat, Quantity = 3 });
            await db.SaveChangesAsync();

            return token;
        }

        // DEMO-001: valid, ready to scan today.
        await CreateShowcaseTokenAsync("SRQR-DEMO-001", todayDate, TokenStatus.Confirmed, null);

        // DEMO-002: expired — booked for a date that has already passed.
        await CreateShowcaseTokenAsync("SRQR-DEMO-002", todayDate.AddDays(-3), TokenStatus.Confirmed, null);

        // DEMO-003: already used — completed with a real collection record.
        var usedToken = await CreateShowcaseTokenAsync("SRQR-DEMO-003", todayDate.AddDays(-1), TokenStatus.Completed, todayDate.AddDays(-1).AddHours(11));
        var beneficiary = await db.Beneficiaries.FirstAsync(b => b.UserId == rahul.Id);
        db.RationCollections.Add(new RationCollection
        {
            CollectionCode = "COL-DEMO-SHOWCASE",
            TokenId = usedToken.Id,
            BeneficiaryId = beneficiary.Id,
            RationShopId = shopId,
            OperatorUserId = rahul.Id,
            VerificationMethod = "QR",
            CollectedAt = usedToken.CollectedAt!.Value,
            Items = [new RationCollectionItem { RationType = RationType.Rice, Quantity = 5 }, new RationCollectionItem { RationType = RationType.Wheat, Quantity = 3 }]
        });
        await db.SaveChangesAsync();
    }

    private static string ComputeQrValue(string secret, int tokenId, string tokenNumber)
    {
        var payload = $"{tokenId}:{tokenNumber}";
        var signatureBytes = HMACSHA256.HashData(Encoding.UTF8.GetBytes(secret), Encoding.UTF8.GetBytes(payload));
        var signature = Convert.ToHexString(signatureBytes)[..16];
        return $"SRQR-{tokenId}-{signature}";
    }
}
