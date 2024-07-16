from fastapi import APIRouter
from .endpoints import login, master,user,branch, vehicle, wallet,booking
from .endpoints import parking_details,manager,export, import_file

api_router = APIRouter()


api_router.include_router(login.router, tags=["Login"], prefix="/login")

api_router.include_router(user.router, tags=["User"], prefix="/user")

api_router.include_router(branch.router, tags=["Branch"], prefix="/branch")

api_router.include_router(master.router,tags=['Master'], prefix="/master")

api_router.include_router(vehicle.router, tags=['Vehicle'], prefix="/vehicle")

api_router.include_router(wallet.router, tags=['Wallet'], prefix="/wallet")

api_router.include_router(booking.router, tags=['Booking'], prefix="/booking" )

api_router.include_router(parking_details.router, tags=['ParkingDetails'], prefix="/parkingdetails" )

api_router.include_router(manager.router, tags=['Manager'], prefix="/manager" )

api_router.include_router(export.router, tags=['Export'], prefix="/export" )

api_router.include_router(import_file.router, tags=['Import'], prefix="/import" )
