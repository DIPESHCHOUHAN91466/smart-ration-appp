using Microsoft.EntityFrameworkCore;
using SmartRation.Api.Models;

namespace SmartRation.Api.Data;

// Applies pending migrations and, only if the database is empty, seeds
// reference/demo data so the app is usable immediately after first run.
// Demo accounts intentionally mirror the ones the frontend prototype
// already advertised (rural/shop/officer @example.com, password demo123).
public static class DbInitializer
{
    public static async Task InitializeAsync(SmartRationDbContext db)
    {
        await db.Database.MigrateAsync();

        if (!await db.RationItems.AnyAsync())
        {
            db.RationItems.AddRange(
                new RationItem { RationType = RationType.Rice, Name = "Rice", VernacularName = "Tandul", Unit = "kg", StandardQuotaPerBooking = 5 },
                new RationItem { RationType = RationType.Wheat, Name = "Wheat", VernacularName = "Gahu", Unit = "kg", StandardQuotaPerBooking = 5 },
                new RationItem { RationType = RationType.Sugar, Name = "Sugar", VernacularName = "Sakhar", Unit = "kg", StandardQuotaPerBooking = 1 }
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
                    Latitude = 21.2472,
                    Longitude = 79.1197,
                    IsActive = true
                }
            );
            await db.SaveChangesAsync();
        }

        var satnavariShop = await db.RationShops.FirstAsync(s => s.ShopCode == "SR-SATNAVARI-001");

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
            var shops = await db.RationShops.ToListAsync();
            foreach (var shop in shops)
            {
                db.Inventory.AddRange(
                    new Inventory { RationShopId = shop.Id, RationType = RationType.Rice, AvailableQuantity = 1850, AllocatedQuantity = 0, MinimumStockLevel = 300 },
                    new Inventory { RationShopId = shop.Id, RationType = RationType.Wheat, AvailableQuantity = 1420, AllocatedQuantity = 0, MinimumStockLevel = 300 },
                    new Inventory { RationShopId = shop.Id, RationType = RationType.Sugar, AvailableQuantity = 620, AllocatedQuantity = 0, MinimumStockLevel = 200 }
                );
            }
            await db.SaveChangesAsync();
        }

        if (!await db.TimeSlots.AnyAsync())
        {
            var shops = await db.RationShops.ToListAsync();
            var today = DateTime.UtcNow.Date;

            foreach (var shop in shops)
            {
                for (var dayOffset = 0; dayOffset < 3; dayOffset++)
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
                            Capacity = 5,
                            BookedCount = 0
                        });
                    }
                }
            }

            await db.SaveChangesAsync();
        }
    }
}
